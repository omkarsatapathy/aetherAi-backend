"""Product Search Agent for Google ADK - Searches multiple e-commerce sites for products.

This agent performs deep research across multiple e-commerce platforms to find products
matching user preferences. It extracts product URLs, images, prices, and basic details.
"""
from typing import Optional, Callable
from google.adk.agents import LlmAgent
from ..tools import (
    google_search_tool,
    fetch_url_content_tool,
    fetch_multiple_urls_tool,
    datetime_ist_tool,
    extract_product_image_tool,
    extract_product_images_batch_tool,
)
from ....config import Config
from ....logging_config import get_logger

logger = get_logger("chatbot.adk_product_search")


def create_product_search_agent(
    before_agent_callback: Optional[Callable] = None,
    after_agent_callback: Optional[Callable] = None,
    before_model_callback: Optional[Callable] = None,
    after_model_callback: Optional[Callable] = None,
    before_tool_callback: Optional[Callable] = None,
    after_tool_callback: Optional[Callable] = None,
) -> LlmAgent:
    """
    Create and return the Product Search Agent.

    This agent searches multiple e-commerce sites (Amazon, Walmart, BestBuy, etc.)
    to find products matching user preferences. It performs 4-6 targeted searches
    and extracts product information.

    Args:
        before_agent_callback: Callback before agent execution
        after_agent_callback: Callback after agent execution
        before_model_callback: Callback before model call
        after_model_callback: Callback after model call
        before_tool_callback: Callback before tool execution
        after_tool_callback: Callback after tool execution

    Returns:
        LlmAgent configured as the Product Search Agent
    """
    product_search_agent = LlmAgent(
        name="ProductSearchAgent",
        model=Config.GEMINI_MODEL_ID,
        description=(
            "I am the Product Search Agent. I search multiple e-commerce websites "
            "(Amazon, Walmart, BestBuy, eBay, etc.) to find products matching user preferences. "
            "I extract product URLs, images, prices, and details from search results. "
            "Use me when you have user preferences and need to find actual products to recommend."
        ),
        tools=[
            google_search_tool,
            fetch_url_content_tool,
            fetch_multiple_urls_tool,
            datetime_ist_tool,
            extract_product_image_tool,
            extract_product_images_batch_tool,
        ],
        instruction=Config.get_product_search_agent_prompt(),
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

    logger.info(f"Created Product Search Agent: {product_search_agent.name}")
    logger.info(f"Tools: {len(product_search_agent.tools)}")

    return product_search_agent


# For direct usage/testing
if __name__ == "__main__":
    agent = create_product_search_agent()
    print(f"Created agent: {agent.name}")
    print(f"Model: {agent.model}")
    print(f"Tools: {len(agent.tools)}")
