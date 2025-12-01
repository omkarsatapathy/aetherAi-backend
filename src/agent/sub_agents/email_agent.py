"""Email Reading Agent - Handles email-related tasks."""
import os
from google.adk.agents import LlmAgent
from ...tools.tools_factory.build_adk_tools import (
    gmail_messages_tool,
    gmail_auth_tool,
    datetime_ist_tool
)


def create_email_agent() -> LlmAgent:
    """
    Create and return the Email Reading Agent.

    This agent specializes in:
    - Reading Gmail messages
    - Checking email authentication status
    - Providing current date/time context for emails

    Returns:
        LlmAgent configured with email-related tools
    """
    email_agent = LlmAgent(
        name="EmailAgent",
        model=os.getenv("GEMINI_MODEL_ID", "gemini-2.5-flash-exp"),
        description=(
            "I am the Email Reading Agent. I specialize in reading and managing Gmail messages. "
            "I can fetch recent emails, check authentication status, and provide email summaries. "
            "Use me when users ask about their emails, inbox, messages from specific senders, "
            "or need to check unread emails."
        ),
        tools=[
            gmail_messages_tool,
            gmail_auth_tool,
            datetime_ist_tool
        ],
        instruction=(
            "You are an expert email assistant. When users ask about emails:\n"
            "1. First check if they are authenticated using gmail_auth_status\n"
            "2. Fetch relevant emails using fetch_gmail_messages with appropriate query parameters\n"
            "3. Provide clear, organized summaries of emails\n"
            "4. Use datetime_ist_tool to provide context about email timing\n"
            "5. Be helpful in filtering and organizing email information\n"
            "6. Always respect user privacy and only share information they request"
        )
    )

    return email_agent


# For direct usage
if __name__ == "__main__":
    agent = create_email_agent()
    print(f"Created agent: {agent.name}")
    print(f"Model: {agent.model}")
    print(f"Tools: {len(agent.tools)}")
