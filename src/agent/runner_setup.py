"""Runner setup for the multi-agent system."""
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from .coordinator_agent import create_coordinator_agent

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Configuration
APP_NAME = "AetherAI_MultiAgent_System"
DEFAULT_USER_ID = "user_001"


class AgentRunner:
    """
    Manages the multi-agent system with Runner and Session management.

    This class provides a clean interface for:
    - Initializing the multi-agent system
    - Managing user sessions
    - Running agent interactions
    - Handling async operations
    """

    def __init__(self, app_name: str = APP_NAME):
        """
        Initialize the AgentRunner.

        Args:
            app_name: Name of the application for session management
        """
        self.app_name = app_name
        self.session_service = InMemorySessionService()
        self.coordinator_agent = create_coordinator_agent()
        self.runner = None

        # Verify API key is set
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in environment variables. "
                "Please set it in your .env file."
            )

        # Set the API key for Google GenAI
        os.environ['GOOGLE_API_KEY'] = api_key

        print(f"✓ AgentRunner initialized for '{self.app_name}'")
        print(f"✓ Coordinator agent loaded: {self.coordinator_agent.name}")
        print(f"✓ Sub-agents: {len(self.coordinator_agent.sub_agents)}")

    def _initialize_runner(self):
        """Initialize the Runner with the coordinator agent."""
        if self.runner is None:
            self.runner = Runner(
                agent=self.coordinator_agent,
                app_name=self.app_name,
                session_service=self.session_service
            )
            print(f"✓ Runner created for agent '{self.runner.agent.name}'")

    async def create_session(
        self,
        user_id: str = DEFAULT_USER_ID,
        session_id: str = None,
        initial_state: dict = None
    ) -> str:
        """
        Create a new session for a user.

        Args:
            user_id: Unique identifier for the user
            session_id: Optional session identifier (auto-generated if not provided)
            initial_state: Optional initial state dictionary

        Returns:
            The session_id that was created
        """
        if session_id is None:
            import uuid
            session_id = f"session_{uuid.uuid4().hex[:8]}"

        await self.session_service.create_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id,
            state=initial_state or {}
        )

        print(f"✓ Session created: {session_id} for user: {user_id}")
        return session_id

    async def run_query(
        self,
        query: str,
        user_id: str = DEFAULT_USER_ID,
        session_id: str = None
    ) -> str:
        """
        Run a query through the agent system.

        Args:
            query: The user's query/message
            user_id: User identifier
            session_id: Session identifier (creates new session if not provided)

        Returns:
            The agent's final response as a string
        """
        # Initialize runner if needed
        self._initialize_runner()

        # Create session if not provided
        if session_id is None:
            session_id = await self.create_session(user_id=user_id)

        # Create the message content
        content = types.Content(
            role='user',
            parts=[types.Part(text=query)]
        )

        print(f"\n{'='*60}")
        print(f"User Query: {query}")
        print(f"{'='*60}\n")

        # Run the agent and collect response
        final_response = ""
        async for event in self.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content
        ):
            # Handle different event types
            if event.is_final_response():
                final_response = event.content.parts[0].text
                print(f"\n{'='*60}")
                print(f"Agent Response:")
                print(f"{'='*60}")
                print(final_response)
                print(f"{'='*60}\n")
                break

        return final_response

    async def run_interactive_session(
        self,
        user_id: str = DEFAULT_USER_ID,
        session_id: str = None
    ):
        """
        Run an interactive chat session with the agent system.

        Args:
            user_id: User identifier
            session_id: Optional session identifier (creates new if not provided)
        """
        # Create session
        if session_id is None:
            session_id = await self.create_session(user_id=user_id)

        print("\n" + "="*60)
        print("AetherAI Multi-Agent Interactive Session")
        print("="*60)
        print(f"Session ID: {session_id}")
        print(f"User ID: {user_id}")
        print("\nAvailable agents:")
        print("  - EmailAgent: Email reading and management")
        print("  - NewsReaderAgent: News briefs and storytelling")
        print("  - MapsAgent: Location and navigation")
        print("  - ResearcherAgent: Deep research and analysis")
        print("\nType 'quit' or 'exit' to end the session")
        print("="*60 + "\n")

        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\nEnding session. Goodbye!")
                    break

                # Run the query
                await self.run_query(
                    query=user_input,
                    user_id=user_id,
                    session_id=session_id
                )

            except KeyboardInterrupt:
                print("\n\nSession interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\nError: {str(e)}")
                print("Continuing session...\n")


# Convenience function for single queries
async def run_single_query(query: str) -> str:
    """
    Run a single query without managing sessions manually.

    Args:
        query: The user's query

    Returns:
        The agent's response
    """
    runner = AgentRunner()
    response = await runner.run_query(query)
    return response


# Main entry point for testing
async def main():
    """Main function for testing the agent system."""
    runner = AgentRunner()

    # Example 1: Single query
    print("\n" + "="*60)
    print("Example 1: Email Query")
    print("="*60)
    await runner.run_query("Show me my recent emails")

    # Example 2: News query
    print("\n" + "="*60)
    print("Example 2: News Query")
    print("="*60)
    await runner.run_query("Give me today's top news headlines")

    # Example 3: Location query
    print("\n" + "="*60)
    print("Example 3: Location Query")
    print("="*60)
    await runner.run_query("Find nearby Italian restaurants")

    # Example 4: Research query
    print("\n" + "="*60)
    print("Example 4: Research Query")
    print("="*60)
    await runner.run_query("Research the latest developments in quantum computing")

    # Uncomment to run interactive session
    # await runner.run_interactive_session()


if __name__ == "__main__":
    asyncio.run(main())
