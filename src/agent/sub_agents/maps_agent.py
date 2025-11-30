"""Google Maps Agent - Handles location and navigation tasks."""
import os
from google.adk.agents import LlmAgent
from ...tools.tools_factory.build_adk_tools import (
    search_nearby_places_tool,
    get_directions_tool,
    get_traffic_info_tool,
    get_place_details_tool,
    explore_area_tool,
    datetime_ist_tool
)


def create_maps_agent() -> LlmAgent:
    """
    Create and return the Google Maps Agent.

    This agent specializes in:
    - Finding nearby places and businesses
    - Providing directions between locations
    - Checking traffic conditions
    - Getting detailed information about places
    - Exploring areas and recommendations

    Returns:
        LlmAgent configured with maps and location tools
    """
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
        instruction=(
            "You are an expert navigation and location assistant. When users ask about locations:\n"
            "1. Use search_nearby_places_tool to find restaurants, shops, services near them\n"
            "2. Use get_directions_tool to provide routes and travel information between locations\n"
            "3. Use get_traffic_info_tool to check current traffic conditions and best travel times\n"
            "4. Use get_place_details_tool to get operating hours, ratings, reviews, and contact info\n"
            "5. Use explore_area_tool to discover interesting places based on user interests\n"
            "6. Use datetime_ist_tool to provide time-relevant recommendations (breakfast, lunch, dinner spots)\n"
            "7. Provide clear, actionable location information\n"
            "8. Include relevant details like distance, estimated time, and specific addresses\n"
            "9. Consider user context like time of day for recommendations\n"
            "10. Offer alternatives when appropriate (e.g., multiple route options)"
        )
    )

    return maps_agent


# For direct usage
if __name__ == "__main__":
    agent = create_maps_agent()
    print(f"Created agent: {agent.name}")
    print(f"Model: {agent.model}")
    print(f"Tools: {len(agent.tools)}")
