"""Agent package for the chatbot.

This package provides Google ADK (Agent Development Kit) implementation for multi-agent systems.

Features:
- Multi-agent coordination with sub-agents
- Streaming responses via SSE
- Tool execution with limits and callbacks
- Email, News, Maps, and Research agents
- Support for multiple LLM providers via LiteLLM
"""

# Google ADK multi-agent system with streaming support
from .google_adk import (
    # Streaming
    create_adk_streaming_response,
    # Coordinator
    create_coordinator_agent,
    # Runner
    ADKAgentRunner,
    run_adk_query,
    # Callbacks
    ADKCallbackHandler,
    ToolLimitCallback,
    StreamingCallbackContext,
    # Sub-agents
    create_email_agent,
    create_news_reader_agent,
    create_maps_agent,
    create_researcher_agent,
)

__all__ = [
    # Streaming
    'create_adk_streaming_response',

    # Coordinator
    'create_coordinator_agent',

    # Runner
    'ADKAgentRunner',
    'run_adk_query',

    # Callbacks
    'ADKCallbackHandler',
    'ToolLimitCallback',
    'StreamingCallbackContext',

    # Sub-agents
    'create_email_agent',
    'create_news_reader_agent',
    'create_maps_agent',
    'create_researcher_agent',
]
