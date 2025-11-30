"""Runner setup for the Google ADK multi-agent system.

This module provides the ADKAgentRunner class that manages:
- Session management with InMemorySessionService
- Runner initialization with the coordinator agent
- Query execution via run_async
- Interactive chat sessions
"""
import os
import asyncio
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .coordinator_agent import create_coordinator_agent, create_coordinator_with_context
from .callbacks import ADKCallbackHandler, StreamingCallbackContext
from ...config import Config
from ...logging_config import get_logger

logger = get_logger("chatbot.adk_runner")

# Load environment variables
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Configuration
APP_NAME = "AetherAI_ADK_MultiAgent"
DEFAULT_USER_ID = "user_001"


class ADKAgentRunner:
    """
    Manages the Google ADK multi-agent system with Runner and Session management.

    This class provides a clean interface for:
    - Initializing the multi-agent system
    - Managing user sessions
    - Running agent interactions
    - Handling async operations
    - Streaming responses
    """

    def __init__(self, app_name: str = APP_NAME):
        """
        Initialize the ADKAgentRunner.

        Args:
            app_name: Name of the application for session management
        """
        self.app_name = app_name
        self.session_service = InMemorySessionService()
        self.coordinator_agent = None
        self.callback_handler = None
        self.streaming_context = None
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

        logger.info(f"✓ ADKAgentRunner initialized for '{self.app_name}'")

    def _initialize_runner(self, with_callbacks: bool = True):
        """
        Initialize the Runner with the coordinator agent.
        
        Args:
            with_callbacks: Whether to create agents with callback handlers
        """
        if self.runner is None:
            if with_callbacks:
                # Create coordinator with callback handler and context
                self.coordinator_agent, self.callback_handler, self.streaming_context = \
                    create_coordinator_with_context()
                print(f"✓ Callback handler and streaming context initialized")
            else:
                # Create coordinator without callbacks
                self.coordinator_agent = create_coordinator_agent()
            
            self.runner = Runner(
                agent=self.coordinator_agent,
                app_name=self.app_name,
                session_service=self.session_service
            )
            
            logger.info(f"✓ Runner created for agent '{self.runner.agent.name}'")
            logger.info(f"✓ Sub-agents: {len(self.coordinator_agent.sub_agents)}")
            for sub_agent in self.coordinator_agent.sub_agents:
                logger.info(f"  - {sub_agent.name}: {len(sub_agent.tools)} tools")

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
            session_id = f"session_{uuid.uuid4().hex[:8]}"

        await self.session_service.create_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id,
            state=initial_state or {}
        )

        logger.info(f"✓ Session created: {session_id} for user: {user_id}")
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

        logger.info(f"\n{'='*60}")
        logger.info(f"User Query: {query}")
        logger.info(f"{'='*60}\n")

        # Run the agent and collect response
        final_response = ""
        current_agent = "CoordinatorAgent"
        
        async for event in self.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content
        ):
            # Track agent changes
            author = getattr(event, 'author', None)
            if author and author != 'user' and author != current_agent:
                current_agent = author
                logger.info(f"🔄 {current_agent} taking control")

            # Handle different event types
            if event.is_final_response():
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            final_response = part.text
                            break
                
                logger.info(f"\n{'='*60}")
                logger.info(f"Agent Response from {current_agent}:")
                logger.info(f"{'='*60}")
                logger.info(final_response[:500] + "..." if len(final_response) > 500 else final_response)
                logger.info(f"{'='*60}\n")
                break

            # Log function calls
            function_calls = event.get_function_calls() if hasattr(event, 'get_function_calls') else []
            if function_calls:
                for call in function_calls:
                    logger.info(f"🔧 Tool call: {call.name}")

        return final_response

    async def run_streaming_query(
        self,
        query: str,
        user_id: str = DEFAULT_USER_ID,
        session_id: str = None
    ):
        """
        Run a streaming query through the agent system.

        This method yields events as they occur, suitable for SSE streaming.

        Args:
            query: The user's query/message
            user_id: User identifier
            session_id: Session identifier (creates new session if not provided)

        Yields:
            Event dictionaries with type and data
        """
        # Initialize runner if needed
        self._initialize_runner(with_callbacks=True)

        # Create session if not provided
        if session_id is None:
            session_id = await self.create_session(user_id=user_id)

        # Create the message content
        content = types.Content(
            role='user',
            parts=[types.Part(text=query)]
        )

        logger.info(f"Starting streaming query: {query}")

        current_agent = "CoordinatorAgent"
        tool_count = 0

        async for event in self.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content
        ):
            # Get pending events from callback handler
            if self.streaming_context:
                for cb_event in self.streaming_context.get_pending_events():
                    yield cb_event

            # Track agent changes
            author = getattr(event, 'author', None)
            if author and author != 'user' and author != current_agent:
                current_agent = author
                yield {
                    'event_type': 'thinking',
                    'data': {'status': f'{current_agent} working...'}
                }

            # Handle function calls
            function_calls = event.get_function_calls() if hasattr(event, 'get_function_calls') else []
            if function_calls:
                for call in function_calls:
                    tool_count += 1
                    yield {
                        'event_type': 'tool',
                        'data': {
                            'tool_name': call.name,
                            'tool_count': tool_count,
                            'max_tools': Config.MAX_TOOL_CALLS
                        }
                    }

            # Handle text content
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        is_partial = getattr(event, 'partial', False)
                        if is_partial or event.is_final_response():
                            yield {
                                'event_type': 'message',
                                'data': {'chunk': part.text}
                            }

            # Check for completion
            if event.is_final_response():
                yield {
                    'event_type': 'done',
                    'data': {
                        'status': 'Done!' if tool_count == 0 else f'Done! (used {tool_count} tools)',
                        'tool_count': tool_count
                    }
                }
                break

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
        print("AetherAI ADK Multi-Agent Interactive Session")
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
async def run_adk_query(query: str) -> str:
    """
    Run a single query without managing sessions manually.

    Args:
        query: The user's query

    Returns:
        The agent's response
    """
    runner = ADKAgentRunner()
    response = await runner.run_query(query)
    return response


# Main entry point for testing
async def main():
    """Main function for testing the ADK agent system."""
    runner = ADKAgentRunner()

    # Example 1: Simple greeting
    print("\n" + "="*60)
    print("Example 1: Simple Greeting")
    print("="*60)
    await runner.run_query("Hello! What can you help me with?")

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

    # Uncomment to run interactive session
    # await runner.run_interactive_session()


if __name__ == "__main__":
    asyncio.run(main())
