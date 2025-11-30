"""
ADK Agents - Multi-Agent System for AetherAI

This module provides a complete multi-agent system with:
- Coordinator Agent (parent): Routes requests to specialist agents
- Email Agent: Handles Gmail reading and management
- News Reader Agent: Provides news briefs and storytelling
- Maps Agent: Handles location, navigation, and places
- Researcher Agent: Conducts deep research and formal analysis

Usage:
    Basic usage with AgentRunner:
    ```python
    import asyncio
    from src.agent import AgentRunner

    async def main():
        runner = AgentRunner()
        response = await runner.run_query("Show me my recent emails")
        print(response)

    asyncio.run(main())
    ```

    Interactive session:
    ```python
    async def main():
        runner = AgentRunner()
        await runner.run_interactive_session()

    asyncio.run(main())
    ```

    Single query convenience function:
    ```python
    from src.agent import run_single_query

    response = await run_single_query("Give me today's news")
    ```

For more details, see:
- coordinator_agent.py: Parent agent that manages delegation
- sub_agents/: Individual specialist agent definitions
- runner_setup.py: Runner and session management
"""

from .coordinator_agent import create_coordinator_agent
from .runner_setup import AgentRunner, run_single_query
from .sub_agents import (
    create_email_agent,
    create_news_reader_agent,
    create_maps_agent,
    create_researcher_agent
)

__all__ = [
    'create_coordinator_agent',
    'AgentRunner',
    'run_single_query',
    'create_email_agent',
    'create_news_reader_agent',
    'create_maps_agent',
    'create_researcher_agent'
]
