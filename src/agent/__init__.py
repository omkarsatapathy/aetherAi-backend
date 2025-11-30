"""Agent package for the chatbot."""
# Legacy streaming agent
from .streaming_agent import create_streaming_response

# New multi-agent system
from .coordinator_agent import create_coordinator_agent
from .runner_setup import AgentRunner, run_single_query
from .sub_agents import (
    create_email_agent,
    create_news_reader_agent,
    create_maps_agent,
    create_researcher_agent
)

__all__ = [
    # Legacy
    'create_streaming_response',
    # Multi-agent system
    'create_coordinator_agent',
    'AgentRunner',
    'run_single_query',
    'create_email_agent',
    'create_news_reader_agent',
    'create_maps_agent',
    'create_researcher_agent'
]
