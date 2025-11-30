"""Coordinator Agent for Google ADK - Parent agent that manages all sub-agents.

This module implements the coordinator agent using Google ADK's LlmAgent with 
sub-agents. It supports streaming via callbacks for real-time updates.

Supports multiple model providers via LiteLLM:
- Gemini (native): "gemini-2.0-flash"
- OpenAI: "openai/gpt-4o"
- Anthropic: "anthropic/claude-3-5-sonnet-20241022"
- Ollama: "ollama_chat/llama3.2"
"""
import os
from typing import Optional, Callable, Dict, Any, Union
from google.adk.agents import LlmAgent
from .sub_agents import (
    create_email_agent,
    create_news_reader_agent,
    create_maps_agent,
    create_researcher_agent
)
from .callbacks import ADKCallbackHandler, StreamingCallbackContext
from .tools import datetime_ist_tool
from .model_providers import get_adk_model, ADKModelProviderFactory
from ...config import Config
from ...logging_config import get_logger

logger = get_logger("chatbot.adk_coordinator")


def create_coordinator_agent(
    callback_handler: Optional[ADKCallbackHandler] = None,
    streaming_context: Optional[StreamingCallbackContext] = None,
    model_provider: Optional[str] = None,
) -> LlmAgent:
    """
    Create and return the Coordinator Agent with all sub-agents.

    This is the parent agent that coordinates and delegates tasks to specialized sub-agents:
    - EmailAgent: Handles email reading and management
    - NewsReaderAgent: Provides news briefs and story-telling
    - MapsAgent: Handles location, navigation, and places
    - ResearcherAgent: Conducts deep research and formal analysis

    The coordinator uses LLM-driven delegation to route user requests to the appropriate
    specialist agent based on the request context.

    Args:
        callback_handler: Optional ADKCallbackHandler for streaming support
        streaming_context: Optional context for streaming events
        model_provider: Model provider string, e.g.:
            - "gemini-2.0-flash" (default, native Gemini)
            - "openai/gpt-4o" (OpenAI via LiteLLM)
            - "anthropic/claude-3-5-sonnet-20241022" (Anthropic via LiteLLM)
            - "ollama_chat/llama3.2" (Ollama via LiteLLM)

    Returns:
        LlmAgent configured as the coordinator with all sub-agents
    """
    # Create callback handler if not provided
    if callback_handler is None:
        streaming_context = streaming_context or StreamingCallbackContext()
        callback_handler = ADKCallbackHandler(
            max_tool_calls=Config.MAX_TOOL_CALLS,
            streaming_context=streaming_context
        )

    # Get callbacks dict from handler
    callbacks = callback_handler.get_callbacks_dict()

    # Create all sub-agents with shared callbacks
    email_agent = create_email_agent(
        before_agent_callback=callbacks.get('before_agent_callback'),
        after_agent_callback=callbacks.get('after_agent_callback'),
        before_model_callback=callbacks.get('before_model_callback'),
        after_model_callback=callbacks.get('after_model_callback'),
        before_tool_callback=callbacks.get('before_tool_callback'),
        after_tool_callback=callbacks.get('after_tool_callback'),
    )
    
    news_reader_agent = create_news_reader_agent(
        before_agent_callback=callbacks.get('before_agent_callback'),
        after_agent_callback=callbacks.get('after_agent_callback'),
        before_model_callback=callbacks.get('before_model_callback'),
        after_model_callback=callbacks.get('after_model_callback'),
        before_tool_callback=callbacks.get('before_tool_callback'),
        after_tool_callback=callbacks.get('after_tool_callback'),
    )
    
    maps_agent = create_maps_agent(
        before_agent_callback=callbacks.get('before_agent_callback'),
        after_agent_callback=callbacks.get('after_agent_callback'),
        before_model_callback=callbacks.get('before_model_callback'),
        after_model_callback=callbacks.get('after_model_callback'),
        before_tool_callback=callbacks.get('before_tool_callback'),
        after_tool_callback=callbacks.get('after_tool_callback'),
    )
    
    researcher_agent = create_researcher_agent(
        before_agent_callback=callbacks.get('before_agent_callback'),
        after_agent_callback=callbacks.get('after_agent_callback'),
        before_model_callback=callbacks.get('before_model_callback'),
        after_model_callback=callbacks.get('after_model_callback'),
        before_tool_callback=callbacks.get('before_tool_callback'),
        after_tool_callback=callbacks.get('after_tool_callback'),
    )

    # Get the model - supports Gemini (native) and other providers via LiteLLM
    if model_provider:
        try:
            model = get_adk_model(model_provider)
            logger.info(f"Using model provider: {model_provider}")
        except ValueError as e:
            logger.warning(f"Model provider '{model_provider}' not available: {e}. Falling back to default Gemini.")
            model = os.getenv("GEMINI_MODEL_ID", "gemini-2.0-flash")
    else:
        model = os.getenv("GEMINI_MODEL_ID", "gemini-2.0-flash")
        logger.info(f"Using default Gemini model: {model}")

    # Create the coordinator parent agent (uses datetime_ist_tool from tools module)
    coordinator = LlmAgent(
        name="CoordinatorAgent",
        model=model,
        description=(
            "I am the Coordinator Agent. I manage a team of specialized agents and route "
            "user requests to the most appropriate specialist. My team includes:\n"
            "- EmailAgent: For reading and managing Gmail messages\n"
            "- NewsReaderAgent: For news updates, morning briefs, and engaging news delivery\n"
            "- MapsAgent: For locations, directions, traffic, and place recommendations\n"
            "- ResearcherAgent: For deep research, formal reports, and analytical investigations"
        ),
        # Sub-agents for delegation
        sub_agents=[
            email_agent,
            news_reader_agent,
            maps_agent,
            researcher_agent
        ],
        # Coordinator's own tools
        tools=[datetime_ist_tool],
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
            "   - Requests that don't fit any specialist\n"
            "   - Date/time queries (use get_current_datetime_ist)\n\n"

            "5. DELEGATION PROCESS:\n"
            "   - Use the transfer_to_agent() function to delegate\n"
            "   - Provide context when transferring\n"
            "   - Let the specialist handle their domain\n\n"

            "6. RESPONSE STYLE:\n"
            "   - Be friendly and helpful\n"
            "   - Clearly indicate when delegating to a specialist\n"
            "   - Summarize results from specialists when needed\n\n"

            "Remember: You are a coordinator, not a specialist. Delegate to experts whenever appropriate."
        ),
        # Agent Lifecycle Callbacks
        before_agent_callback=callbacks.get('before_agent_callback'),
        after_agent_callback=callbacks.get('after_agent_callback'),
        # LLM Interaction Callbacks  
        before_model_callback=callbacks.get('before_model_callback'),
        after_model_callback=callbacks.get('after_model_callback'),
        # Tool Execution Callbacks
        before_tool_callback=callbacks.get('before_tool_callback'),
        after_tool_callback=callbacks.get('after_tool_callback'),
    )

    logger.info(f"Created coordinator agent: {coordinator.name}")
    logger.info(f"Model: {coordinator.model}")
    logger.info(f"Sub-agents: {len(coordinator.sub_agents)}")
    for sub_agent in coordinator.sub_agents:
        logger.info(f"  - {sub_agent.name}: {len(sub_agent.tools)} tools")

    return coordinator


def create_coordinator_with_context() -> tuple[LlmAgent, ADKCallbackHandler, StreamingCallbackContext]:
    """
    Create a coordinator agent with its callback handler and streaming context.
    
    This is useful when you need access to the streaming context for SSE events.
    
    Returns:
        Tuple of (coordinator_agent, callback_handler, streaming_context)
    """
    context = StreamingCallbackContext(max_tool_calls=Config.MAX_TOOL_CALLS)
    handler = ADKCallbackHandler(
        max_tool_calls=Config.MAX_TOOL_CALLS,
        streaming_context=context
    )
    coordinator = create_coordinator_agent(
        callback_handler=handler,
        streaming_context=context
    )
    
    return coordinator, handler, context


# For direct usage/testing
if __name__ == "__main__":
    agent = create_coordinator_agent()
    print(f"Created coordinator agent: {agent.name}")
    print(f"Model: {agent.model}")
    print(f"Sub-agents: {len(agent.sub_agents)}")
    for sub_agent in agent.sub_agents:
        print(f"  - {sub_agent.name}: {len(sub_agent.tools)} tools")
