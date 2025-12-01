"""Email Reading Agent for Google ADK - Handles email-related tasks."""
from typing import Optional, Callable, Any
from google.adk.agents import LlmAgent
from ..tools import (
    gmail_messages_tool,
    gmail_auth_tool,
    datetime_ist_tool
)
from ....config import Config


def create_email_agent(
    before_agent_callback: Optional[Callable] = None,
    after_agent_callback: Optional[Callable] = None,
    before_model_callback: Optional[Callable] = None,
    after_model_callback: Optional[Callable] = None,
    before_tool_callback: Optional[Callable] = None,
    after_tool_callback: Optional[Callable] = None,
) -> LlmAgent:
    """
    Create and return the Email Reading Agent with ADK callbacks.

    This agent specializes in:
    - Reading Gmail messages
    - Checking email authentication status
    - Providing current date/time context for emails

    Args:
        before_agent_callback: Called before agent execution
        after_agent_callback: Called after agent execution
        before_model_callback: Called before LLM call
        after_model_callback: Called after LLM response
        before_tool_callback: Called before tool execution
        after_tool_callback: Called after tool execution

    Returns:
        LlmAgent configured with email-related tools and callbacks
    """
    # Use pre-wrapped FunctionTools from the tools module
    email_agent = LlmAgent(
        name="EmailAgent",
        model=Config.GEMINI_MODEL_ID,
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
        ),
        # Agent Lifecycle Callbacks
        before_agent_callback=before_agent_callback,
        after_agent_callback=after_agent_callback,
        # LLM Interaction Callbacks
        before_model_callback=before_model_callback,
        after_model_callback=after_model_callback,
        # Tool Execution Callbacks
        before_tool_callback=before_tool_callback,
        after_tool_callback=after_tool_callback,
    )

    return email_agent


# For direct usage/testing
if __name__ == "__main__":
    agent = create_email_agent()
    print(f"Created agent: {agent.name}")
    print(f"Model: {agent.model}")
    print(f"Tools: {len(agent.tools)}")
