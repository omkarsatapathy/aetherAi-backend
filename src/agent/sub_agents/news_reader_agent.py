"""News Reader Agent - Handles news and story briefings."""
import os
from google.adk.agents import LlmAgent
from ...tools.tools_factory.build_adk_tools import (
    google_search_tool,
    fetch_url_content_tool,
    fetch_multiple_urls_tool,
    datetime_ist_tool
)


def create_news_reader_agent() -> LlmAgent:
    """
    Create and return the News Reader Agent.

    This agent specializes in:
    - Reading and summarizing news articles
    - Providing morning news briefs
    - Story-telling format for news delivery
    - Quick news updates and headlines

    Returns:
        LlmAgent configured with news reading tools
    """
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
            "1. Use google_search_tool to find relevant, recent news articles\n"
            "2. Fetch article content using fetch_url_content_tool for detailed information\n"
            "3. For multiple news items, use fetch_multiple_urls_tool efficiently\n"
            "4. Use datetime_ist_tool to provide time context (e.g., 'This morning's news')\n"
            "5. Present news in an engaging, storytelling format - not just dry facts\n"
            "6. For morning briefs, organize by categories: top news, business, tech, sports, etc.\n"
            "7. Keep tone conversational and friendly, like a radio news presenter\n"
            "8. Prioritize recent, credible news sources\n"
            "9. Provide context and background when needed for complex stories\n"
            "10. End with a brief summary or key takeaway"
        )
    )

    return news_reader_agent


# For direct usage
if __name__ == "__main__":
    agent = create_news_reader_agent()
    print(f"Created agent: {agent.name}")
    print(f"Model: {agent.model}")
    print(f"Tools: {len(agent.tools)}")
