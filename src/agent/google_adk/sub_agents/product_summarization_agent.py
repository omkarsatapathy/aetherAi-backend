"""Product Summarization Agent for Google ADK - Formats product recommendations.

This agent consolidates raw product data from the Product Search Agent, filters duplicates,
ranks by user preferences, and creates engaging product descriptions in the required JSON format.
"""
from typing import Optional, Callable
from google.adk.agents import LlmAgent
from ....config import Config
from ....logging_config import get_logger

logger = get_logger("chatbot.adk_product_summarization")


def create_product_summarization_agent(
    before_agent_callback: Optional[Callable] = None,
    after_agent_callback: Optional[Callable] = None,
    before_model_callback: Optional[Callable] = None,
    after_model_callback: Optional[Callable] = None,
    before_tool_callback: Optional[Callable] = None,
    after_tool_callback: Optional[Callable] = None,
) -> LlmAgent:
    """
    Create and return the Product Summarization Agent.

    This agent receives raw product data from ProductSearchAgent, consolidates it,
    removes duplicates, ranks by user preferences, and generates engaging descriptions
    in the required JSON format for frontend display.

    Args:
        before_agent_callback: Callback before agent execution
        after_agent_callback: Callback after agent execution
        before_model_callback: Callback before model call
        after_model_callback: Callback after model call
        before_tool_callback: Callback before tool execution
        after_tool_callback: Callback after tool execution

    Returns:
        LlmAgent configured as the Product Summarization Agent
    """
    product_summarization_agent = LlmAgent(
        name="ProductSummarizationAgent",
        model=Config.GEMINI_MODEL_ID,
        description=(
            "I am the Product Summarization Agent. I take raw product data from searches, "
            "filter duplicates, rank by user preferences, and create engaging product descriptions. "
            "I format the final response as JSON with product recommendations including text descriptions, "
            "image links, and product links. Use me after product search is complete to present "
            "recommendations to the user."
        ),
        tools=[],  # No external tools needed - uses LLM intelligence for summarization
        instruction=Config.get_product_summarization_agent_prompt(),
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

    logger.info(f"Created Product Summarization Agent: {product_summarization_agent.name}")
    logger.info(f"Tools: {len(product_summarization_agent.tools)}")

    return product_summarization_agent


# For direct usage/testing
if __name__ == "__main__":
    agent = create_product_summarization_agent()
    print(f"Created agent: {agent.name}")
    print(f"Model: {agent.model}")
    print(f"Tools: {len(agent.tools)}")
