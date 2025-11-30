"""Agent package for the chatbot.

This package provides two agent implementations:
1. Strands-based agents (streaming_agent.py) - The original implementation using Strands
2. Google ADK agents (google_adk/) - New implementation using Google Agent Development Kit

Both implementations support:
- Multi-agent coordination with sub-agents
- Streaming responses via SSE
- Tool execution with limits
- Email, News, Maps, and Research agents
"""
# Strands-based streaming agent (original implementation)
from .streaming_agent import create_streaming_response

# Original ADK multi-agent system (basic implementation)
from .coordinator_agent import create_coordinator_agent
from .runner_setup import AgentRunner, run_single_query
from .sub_agents import (
    create_email_agent,
    create_news_reader_agent,
    create_maps_agent,
    create_researcher_agent
)

# Google ADK multi-agent system with streaming support
from .google_adk import (
    # Streaming
    create_adk_streaming_response,
    # Coordinator
    create_coordinator_agent as create_adk_coordinator_agent,
    # Runner
    ADKAgentRunner,
    run_adk_query,
    # Callbacks
    ADKCallbackHandler,
    ToolLimitCallback,
    StreamingCallbackContext,
    # Sub-agents (aliased to avoid conflicts)
    create_email_agent as create_adk_email_agent,
    create_news_reader_agent as create_adk_news_reader_agent,
    create_maps_agent as create_adk_maps_agent,
    create_researcher_agent as create_adk_researcher_agent,
)

__all__ = [
    # Strands streaming agent
    'create_streaming_response',
    
    # Original multi-agent system
    'create_coordinator_agent',
    'AgentRunner',
    'run_single_query',
    'create_email_agent',
    'create_news_reader_agent',
    'create_maps_agent',
    'create_researcher_agent',
    
    # Google ADK multi-agent system
    'create_adk_streaming_response',
    'create_adk_coordinator_agent',
    'ADKAgentRunner',
    'run_adk_query',
    'ADKCallbackHandler',
    'ToolLimitCallback',
    'StreamingCallbackContext',
    'create_adk_email_agent',
    'create_adk_news_reader_agent',
    'create_adk_maps_agent',
    'create_adk_researcher_agent',
]
