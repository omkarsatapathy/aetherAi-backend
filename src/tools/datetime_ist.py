"""Tool to get current date and time in IST."""
from datetime import datetime
import pytz
from strands import tool
import os
from pathlib import Path
from dotenv import load_dotenv
from ..config import Config

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Google ADk Import
import asyncio
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# @tool
def get_current_datetime_ist() -> str:
    """
    Strands tool: Get the current date and time in IST (Indian Standard Time).

    Returns:
        String with the current date and time in IST timezone formatted as 'YYYY-MM-DD HH:MM:SS IST'
    """
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S IST')
    print(f'\n\n fetched date and time as {formatted_time}')
    return formatted_time

time_tools  = FunctionTool(func=get_current_datetime_ist)

# Get API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in your .env file.")

# Set the API key as environment variable for Google GenAI
os.environ['GOOGLE_API_KEY'] = GEMINI_API_KEY

time_agent = Agent(
    model=Config.GEMINI_MODEL_ID,
    tools=[time_tools],
    name="TimeAgent",
    description="An agent that provides the current date and time in IST."
)

APP_NAME = "DatetimeISTApp"
USER_ID = "user_123"
SESSION_ID = "session_456"
async def main():
    """Main function to run the agent asynchronously."""
    # Session and Runner Setup
    session_service = InMemorySessionService()
    # Use 'await' to correctly create the session
    await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)

    runner = Runner(agent=time_agent, app_name=APP_NAME, session_service=session_service)

    # Agent Interaction
    query = "what is the current date and time in IST?"
    print(f"User Query: {query}")
    content = types.Content(role='user', parts=[types.Part(text=query)])

    # The runner's run method handles the async loop internally
    events = runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            print("Agent Response:", final_response)

# Standard way to run the main async function
if __name__ == "__main__":
    asyncio.run(main())