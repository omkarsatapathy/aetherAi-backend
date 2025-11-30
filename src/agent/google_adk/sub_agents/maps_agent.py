"""Google Maps Agent for Google ADK - Handles location and navigation tasks."""
import os
from typing import Optional, Callable
from google.adk.agents import LlmAgent
from ..tools import (
    search_nearby_places_tool,
    get_directions_tool,
    get_traffic_info_tool,
    get_place_details_tool,
    explore_area_tool,
    datetime_ist_tool
)
from ....config import Config


def create_maps_agent(
    before_agent_callback: Optional[Callable] = None,
    after_agent_callback: Optional[Callable] = None,
    before_model_callback: Optional[Callable] = None,
    after_model_callback: Optional[Callable] = None,
    before_tool_callback: Optional[Callable] = None,
    after_tool_callback: Optional[Callable] = None,
) -> LlmAgent:
    """
    Create and return the Google Maps Agent with ADK callbacks.

    This agent specializes in:
    - Finding nearby places and businesses
    - Providing directions between locations
    - Checking traffic conditions
    - Getting detailed information about places
    - Exploring areas and recommendations

    Args:
        before_agent_callback: Called before agent execution
        after_agent_callback: Called after agent execution
        before_model_callback: Called before LLM call
        after_model_callback: Called after LLM response
        before_tool_callback: Called before tool execution
        after_tool_callback: Called after tool execution

    Returns:
        LlmAgent configured with maps and location tools and callbacks
    """
    # Use pre-wrapped FunctionTools from the tools module
    maps_agent = LlmAgent(
        name="MapsAgent",
        model=os.getenv("GEMINI_MODEL_ID", "gemini-2.0-flash-exp"),
        description=(
            "I am the Google Maps Agent. I specialize in location-based services, navigation, "
            "and finding places. Use me when users ask about nearby restaurants, directions, "
            "traffic conditions, business details, or want to explore an area. "
            "I can help with travel planning, finding attractions, and getting real-time location information."
        ),
        tools=[
            search_nearby_places_tool,
            get_directions_tool,
            get_traffic_info_tool,
            get_place_details_tool,
            explore_area_tool,
            datetime_ist_tool
        ],
        instruction=Config.get_maps_agent_prompt(),
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

    return maps_agent


# For direct usage/testing
if __name__ == "__main__":
    agent = create_maps_agent()
    print(f"Created agent: {agent.name}")
    print(f"Model: {agent.model}")
    print(f"Tools: {len(agent.tools)}")
