"""Researcher Agent for Google ADK - Handles deep research and formal analysis."""
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


def create_researcher_agent(
    before_agent_callback: Optional[Callable] = None,
    after_agent_callback: Optional[Callable] = None,
    before_model_callback: Optional[Callable] = None,
    after_model_callback: Optional[Callable] = None,
    before_tool_callback: Optional[Callable] = None,
    after_tool_callback: Optional[Callable] = None,
) -> LlmAgent:
    """
    Create and return the Researcher Agent with ADK callbacks.

    This agent specializes in:
    - Conducting deep, comprehensive research
    - Analyzing information from multiple sources
    - Generating formal research reports
    - Creating tables, comparisons, and structured analysis
    - Providing evidence-based recommendations

    Args:
        before_agent_callback: Called before agent execution
        after_agent_callback: Called after agent execution
        before_model_callback: Called before LLM call
        after_model_callback: Called after LLM response
        before_tool_callback: Called before tool execution
        after_tool_callback: Called after tool execution

    Returns:
        LlmAgent configured with research tools and callbacks
    """
    # Use pre-wrapped FunctionTools from the tools module
    researcher_agent = LlmAgent(
        name="ResearcherAgent",
        model=os.getenv("GEMINI_MODEL_ID", "gemini-2.5-flash-exp"),
        description=(
            "I am the Researcher Agent. I specialize in conducting thorough, multi-source research, "
            "and generating formal, comprehensive reports with analysis, tables, and recommendations. "
            "Use me when users need in-depth research, comparative analysis, detailed investigations, "
            "or formal reports on any topic. I provide evidence-based insights and structured analysis."
        ),
        tools=[
            google_search_tool,
            fetch_url_content_tool,
            fetch_multiple_urls_tool,
            datetime_ist_tool
        ],
        instruction=Config.get_researcher_agent_prompt(),
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

    return researcher_agent


# For direct usage/testing
if __name__ == "__main__":
    agent = create_researcher_agent()
    print(f"Created agent: {agent.name}")
    print(f"Model: {agent.model}")
    print(f"Tools: {len(agent.tools)}")
