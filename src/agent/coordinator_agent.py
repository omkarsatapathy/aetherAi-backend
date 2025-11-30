"""Coordinator Agent - Parent agent that manages all sub-agents."""
import os
from google.adk.agents import LlmAgent
from .sub_agents import (
    create_email_agent,
    create_news_reader_agent,
    create_maps_agent,
    create_researcher_agent
)


def create_coordinator_agent() -> LlmAgent:
    """
    Create and return the Coordinator Agent with all sub-agents.

    This is the parent agent that coordinates and delegates tasks to specialized sub-agents:
    - EmailAgent: Handles email reading and management
    - NewsReaderAgent: Provides news briefs and story-telling
    - MapsAgent: Handles location, navigation, and places
    - ResearcherAgent: Conducts deep research and formal analysis

    The coordinator uses LLM-driven delegation to route user requests to the appropriate
    specialist agent based on the request context.

    Returns:
        LlmAgent configured as the coordinator with all sub-agents
    """
    # Create all sub-agents
    email_agent = create_email_agent()
    news_reader_agent = create_news_reader_agent()
    maps_agent = create_maps_agent()
    researcher_agent = create_researcher_agent()

    # Create the coordinator parent agent
    coordinator = LlmAgent(
        name="CoordinatorAgent",
        model=os.getenv("GEMINI_MODEL_ID", "gemini-2.0-flash-exp"),
        description=(
            "I am the Coordinator Agent. I manage a team of specialized agents and route "
            "user requests to the most appropriate specialist. My team includes:\n"
            "- EmailAgent: For reading and managing Gmail messages\n"
            "- NewsReaderAgent: For news updates, morning briefs, and engaging news delivery\n"
            "- MapsAgent: For locations, directions, traffic, and place recommendations\n"
            "- ResearcherAgent: For deep research, formal reports, and analytical investigations"
        ),
        sub_agents=[
            email_agent,
            news_reader_agent,
            maps_agent,
            researcher_agent
        ],
        instruction=(
            "You are the Coordinator Agent managing a team of specialists. Your role is to:\n\n"

            "1. UNDERSTAND USER INTENT:\n"
            "   - Analyze the user's request carefully\n"
            "   - Identify which specialist agent is best suited\n"
            "   - Consider the context and specific needs\n\n"

            "2. ROUTING RULES:\n"
            "   - For EMAIL requests (inbox, messages, unread emails, email from someone):\n"
            "     → Use transfer_to_agent() to delegate to EmailAgent\n"
            "   - For NEWS requests (news brief, headlines, morning news, current events stories):\n"
            "     → Use transfer_to_agent() to delegate to NewsReaderAgent\n"
            "   - For LOCATION requests (directions, nearby places, traffic, restaurants, navigation):\n"
            "     → Use transfer_to_agent() to delegate to MapsAgent\n"
            "   - For RESEARCH requests (detailed analysis, formal report, comparison, investigation):\n"
            "     → Use transfer_to_agent() to delegate to ResearcherAgent\n\n"

            "3. DISTINGUISHING NEWS vs RESEARCH:\n"
            "   - NewsReaderAgent: Quick updates, daily briefing, conversational storytelling\n"
            "   - ResearcherAgent: In-depth analysis, formal reports, multi-source investigation\n\n"

            "4. WHEN TO HANDLE DIRECTLY:\n"
            "   - Simple greetings and general conversation\n"
            "   - Questions about your capabilities\n"
            "   - Requests that don't fit any specialist\n\n"

            "5. DELEGATION PROCESS:\n"
            "   - Use the transfer_to_agent() function to delegate\n"
            "   - Provide context when transferring\n"
            "   - Let the specialist handle their domain\n\n"

            "6. RESPONSE STYLE:\n"
            "   - Be friendly and helpful\n"
            "   - Clearly indicate when delegating to a specialist\n"
            "   - Summarize results from specialists when needed\n\n"

            "Remember: You are a coordinator, not a specialist. Delegate to experts whenever appropriate."
        )
    )

    return coordinator


# For direct usage
if __name__ == "__main__":
    agent = create_coordinator_agent()
    print(f"Created coordinator agent: {agent.name}")
    print(f"Model: {agent.model}")
    print(f"Sub-agents: {len(agent.sub_agents)}")
    for sub_agent in agent.sub_agents:
        print(f"  - {sub_agent.name}: {len(sub_agent.tools)} tools")
