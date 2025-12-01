"""Shopping Assist Agent - Main shopping coordinator that manages preference collection and product search."""
from typing import Optional, Callable
from google.adk.agents import LlmAgent
from .shopping_preference_agent import create_shopping_preference_agent
from .product_search_agent import create_product_search_agent
from .product_summarization_agent import create_product_summarization_agent
from ..tools import (
    google_search_tool,
    fetch_url_content_tool,
    fetch_multiple_urls_tool,
    datetime_ist_tool
)
from ....config import Config


def create_shopping_assist_agent(
    before_agent_callback: Optional[Callable] = None,
    after_agent_callback: Optional[Callable] = None,
    before_model_callback: Optional[Callable] = None,
    after_model_callback: Optional[Callable] = None,
    before_tool_callback: Optional[Callable] = None,
    after_tool_callback: Optional[Callable] = None,
) -> LlmAgent:
    """
    Create and return the Shopping Assist Agent (Main Shopping Coordinator).

    This agent is the main shopping coordinator that:
    - Receives shopping requests from the Coordinator Agent
    - Delegates to ShoppingPreferenceAgent to collect user preferences
    - Delegates to ProductSearchAgent to find products across e-commerce sites
    - Delegates to ProductSummarizationAgent to format final recommendations
    - Returns final product recommendations with links and images

    Args:
        before_agent_callback: Called before agent execution
        after_agent_callback: Called after agent execution
        before_model_callback: Called before LLM call
        after_model_callback: Called after LLM response
        before_tool_callback: Called before tool execution
        after_tool_callback: Called after tool execution

    Returns:
        LlmAgent configured as shopping coordinator with three specialist sub-agents
    """
    # Create all specialist sub-agents
    shopping_preference_agent = create_shopping_preference_agent(
        before_agent_callback=before_agent_callback,
        after_agent_callback=after_agent_callback,
        before_model_callback=before_model_callback,
        after_model_callback=after_model_callback,
        before_tool_callback=before_tool_callback,
        after_tool_callback=after_tool_callback,
    )

    product_search_agent = create_product_search_agent(
        before_agent_callback=before_agent_callback,
        after_agent_callback=after_agent_callback,
        before_model_callback=before_model_callback,
        after_model_callback=after_model_callback,
        before_tool_callback=before_tool_callback,
        after_tool_callback=after_tool_callback,
    )

    product_summarization_agent = create_product_summarization_agent(
        before_agent_callback=before_agent_callback,
        after_agent_callback=after_agent_callback,
        before_model_callback=before_model_callback,
        after_model_callback=after_model_callback,
        before_tool_callback=before_tool_callback,
        after_tool_callback=after_tool_callback,
    )

    # Create the main Shopping Assist Agent
    shopping_assist_agent = LlmAgent(
        name="ShoppingAssistAgent",
        model=Config.GEMINI_MODEL_ID,
        description=(
            "I am the Shopping Assist Agent. I help users buy and shop for products by coordinating "
            "three specialist agents: ShoppingPreferenceAgent (collects preferences), ProductSearchAgent "
            "(searches e-commerce sites), and ProductSummarizationAgent (formats recommendations). "
            "Use me when users want to buy, shop for, or purchase any product."
        ),
        # Three specialist sub-agents for the shopping workflow
        sub_agents=[
            shopping_preference_agent,
            product_search_agent,
            product_summarization_agent
        ],
        # No tools needed - delegates to sub-agents
        tools=[],
        instruction=Config.get_shopping_assist_agent_prompt(),
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

    return shopping_assist_agent


# For direct usage/testing
if __name__ == "__main__":
    agent = create_shopping_assist_agent()
    print(f"Created agent: {agent.name}")
    print(f"Model: {agent.model}")
    print(f"Sub-agents: {len(agent.sub_agents)}")
    print(f"Tools: {len(agent.tools)}")
