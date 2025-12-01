"""Shopping Preference Collector Agent - Researches products and generates preference questions."""
from typing import Optional, Callable
from google.adk.agents import LlmAgent
from ..tools import (
    google_search_tool,
    fetch_url_content_tool,
    fetch_multiple_urls_tool,
    datetime_ist_tool
)
from ....config import Config


def create_shopping_preference_agent(
    before_agent_callback: Optional[Callable] = None,
    after_agent_callback: Optional[Callable] = None,
    before_model_callback: Optional[Callable] = None,
    after_model_callback: Optional[Callable] = None,
    before_tool_callback: Optional[Callable] = None,
    after_tool_callback: Optional[Callable] = None,
) -> LlmAgent:
    """
    Create and return the Shopping Preference Collector Agent.

    This agent specializes in:
    - Researching product categories through web searches
    - Understanding available features, sizes, brands, and price ranges
    - Generating intelligent preference questions based on research
    - Returning structured JSON with questions for user

    Args:
        before_agent_callback: Called before agent execution
        after_agent_callback: Called after agent execution
        before_model_callback: Called before LLM call
        after_model_callback: Called after LLM response
        before_tool_callback: Called before tool execution
        after_tool_callback: Called after tool execution

    Returns:
        LlmAgent configured with search tools and preference collection instructions
    """
    shopping_preference_agent = LlmAgent(
        name="ShoppingPreferenceAgent",
        model=Config.GEMINI_MODEL_ID,
        description=(
            "I am the Shopping Preference Collector Agent. I help users find products by first "
            "researching the product category to understand what's available in the market, then "
            "generating smart preference questions to narrow down their search. Use me when users "
            "want to buy, shop for, or purchase products."
        ),
        tools=[
            google_search_tool,
            fetch_url_content_tool,
            fetch_multiple_urls_tool,
            datetime_ist_tool
        ],
        instruction=Config.get_shopping_preference_agent_prompt(),
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

    return shopping_preference_agent


# For direct usage/testing
if __name__ == "__main__":
    agent = create_shopping_preference_agent()
    print(f"Created agent: {agent.name}")
    print(f"Model: {agent.model}")
    print(f"Tools: {len(agent.tools)}")
