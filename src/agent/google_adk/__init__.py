"""Google ADK Multi-Agent System.

This package contains the Google ADK implementation of the multi-agent system,
featuring streaming support, callbacks, and coordinated sub-agents.

Supports multiple model providers via LiteLLM:
- Gemini (native): "gemini-2.0-flash"
- OpenAI: "openai/gpt-4o"
- Anthropic: "anthropic/claude-3-5-sonnet-20241022"
- Ollama: "ollama_chat/llama3.2"
"""
from .streaming_agent import create_adk_streaming_response
from .coordinator_agent import create_coordinator_agent
from .runner_setup import ADKAgentRunner, run_adk_query
from .callbacks import (
    ADKCallbackHandler,
    ToolLimitCallback,
    StreamingCallbackContext
)
from .sub_agents import (
    create_email_agent,
    create_news_reader_agent,
    create_maps_agent,
    create_researcher_agent
)
from .model_providers import (
    ADKModelProviderFactory,
    get_adk_model,
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
    # Model Providers
    'ADKModelProviderFactory',
    'get_adk_model',
]
