"""Code Generation Agent for Google ADK - Handles code writing, explanation, and debugging.

This agent specializes in all programming-related tasks by leveraging powerful code-focused
models like Gemini 3 Pro. It receives coding requests from the CoordinatorAgent and uses
the generate_code tool to produce high-quality code responses.

Supports:
- Code generation in any programming language
- Code explanation and documentation
- Debugging and error fixing
- Best practices and optimization suggestions
- Algorithm design and implementation
"""
from typing import Optional, Callable
from google.adk.agents import LlmAgent
from ..tools import code_generation_tool, datetime_ist_tool
from ....config import Config


def create_code_generation_agent(
    before_agent_callback: Optional[Callable] = None,
    after_agent_callback: Optional[Callable] = None,
    before_model_callback: Optional[Callable] = None,
    after_model_callback: Optional[Callable] = None,
    before_tool_callback: Optional[Callable] = None,
    after_tool_callback: Optional[Callable] = None,
) -> LlmAgent:
    """
    Create and return the Code Generation Agent with ADK callbacks.

    This agent specializes in:
    - Writing clean, efficient code in any programming language
    - Explaining code and providing documentation
    - Debugging and identifying issues in code
    - Suggesting best practices and optimizations
    - Implementing algorithms and data structures
    - Answering programming conceptual questions

    Args:
        before_agent_callback: Called before agent execution
        after_agent_callback: Called after agent execution
        before_model_callback: Called before LLM call
        after_model_callback: Called after LLM response
        before_tool_callback: Called before tool execution
        after_tool_callback: Called after tool execution

    Returns:
        LlmAgent configured with code generation tools and callbacks
    """
    code_generation_agent = LlmAgent(
        name="CodeGenerationAgent",
        model=Config.GEMINI_MODEL_ID,
        description=(
            "I am the Code Generation Agent. I specialize in all programming-related tasks including "
            "writing code, explaining code, debugging, and providing best practices. I use advanced "
            "code-focused models like Gemini 3 Pro to generate high-quality, well-documented code "
            "in any programming language. Use me when users ask for code, need help understanding "
            "code, want debugging assistance, or have programming questions."
        ),
        tools=[
            code_generation_tool,
            datetime_ist_tool  # Useful for timestamped code comments/docs
        ],
        instruction=Config.get_code_generation_agent_prompt(),
        # Agent Lifecycle Callbacks
        before_agent_callback=before_agent_callback,
        after_agent_callback=after_agent_callback,
        # LLM Interaction Callbacks
        before_model_callback=before_model_callback,
        after_model_callback=after_model_callback,
        # Tool Execution Callbacks
        before_tool_callback=before_tool_callback,
        after_tool_callback=after_tool_callback,
    )

    return code_generation_agent


# For direct usage/testing
if __name__ == "__main__":
    agent = create_code_generation_agent()
    print(f"Created agent: {agent.name}")
    print(f"Model: {agent.model}")
    print(f"Tools: {len(agent.tools)}")
    for tool in agent.tools:
        print(f"  - {tool.name}")
