"""News Reader Agent for Google ADK - Handles news and story briefings."""
import os
from typing import Optional, Callable
from google.adk.agents import LlmAgent
from ..tools import (
    google_search_tool,
    fetch_url_content_tool,
    fetch_multiple_urls_tool,
    datetime_ist_tool
)
from ....config import Config


def create_news_reader_agent(
    before_agent_callback: Optional[Callable] = None,
    after_agent_callback: Optional[Callable] = None,
    before_model_callback: Optional[Callable] = None,
    after_model_callback: Optional[Callable] = None,
    before_tool_callback: Optional[Callable] = None,
    after_tool_callback: Optional[Callable] = None,
) -> LlmAgent:
    """
    Create and return the News Reader Agent with ADK callbacks.

    This agent specializes in:
    - Reading and summarizing news articles
    - Providing morning news briefs
    - Story-telling format for news delivery
    - Quick news updates and headlines

    Args:
        before_agent_callback: Called before agent execution
        after_agent_callback: Called after agent execution
        before_model_callback: Called before LLM call
        after_model_callback: Called after LLM response
        before_tool_callback: Called before tool execution
        after_tool_callback: Called after tool execution

    Returns:
        LlmAgent configured with news reading tools and callbacks
    """
    # Use pre-wrapped FunctionTools from the tools module
    news_reader_agent = LlmAgent(
        name="NewsReaderAgent",
        model=os.getenv("GEMINI_MODEL_ID", "gemini-2.0-flash-exp"),
        description=(
            "I am the News Reader Agent. I specialize in reading news, providing morning briefs, "
            "and delivering news in an engaging storytelling format. "
            "Use me when users ask for news updates, headlines, daily briefings, "
            "or want to hear about current events in a conversational, engaging manner."
        ),
        tools=[
            google_search_tool,
            fetch_url_content_tool,
            fetch_multiple_urls_tool,
            datetime_ist_tool
        ],
        instruction=(
            "You are a professional news reader and storyteller. When users ask for news:\n"
            "1. Use google_search_with_context to find relevant, recent news articles\n"
            "2. Fetch article content using fetch_url_content for detailed information\n"
            "3. For multiple news items, use fetch_multiple_urls efficiently\n"
            "4. Use get_current_datetime_ist to provide time context (e.g., 'This morning's news')\n"
            "5. Present news in an engaging, storytelling format - not just dry facts\n"
            "6. For morning briefs, organize by categories: top news, business, tech, sports, etc.\n"
            "7. Keep tone conversational and friendly, like a radio news presenter\n"
            "8. Prioritize recent, credible news sources\n"
            "9. Provide context and background when needed for complex stories\n"
            "10. End with a brief summary or key takeaway"
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

    return news_reader_agent


# For direct usage/testing
if __name__ == "__main__":
    agent = create_news_reader_agent()
    print(f"Created agent: {agent.name}")
    print(f"Model: {agent.model}")
    print(f"Tools: {len(agent.tools)}")
