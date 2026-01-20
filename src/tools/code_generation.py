"""Code Generation Tool - Invoke specialized LLM for code generation.

This tool wraps code generation models (Gemini 3 Pro, Claude Opus, etc.) to generate
high-quality code based on user queries. Designed to be used by the CodeGenerationAgent.

AUTHENTICATION ARCHITECTURE:
- CodeGenerationAgent (ADK): Uses GEMINI_API_KEY for gemini-2.5-flash (API key auth)
- This Tool: Uses Vertex AI authentication for gemini-3-pro-preview (GCP credentials)

This dual approach allows:
1. Fast, lightweight agent orchestration via API key (gemini-2.5-flash)
2. Powerful code generation via Vertex AI (gemini-3-pro-preview with thinking mode)

Supports multiple models with easy configuration:
- gemini-3-pro-preview (default) - Google's Gemini 3 Pro with thinking capabilities
- claude-opus (future)
- Other models can be added via CODE_GEN_MODELS config
"""
from typing import Optional, Literal
from google import genai
from google.genai.types import GenerateContentConfig, ThinkingConfig
from ..config import Config
from ..logging_config import get_logger

logger = get_logger("chatbot.tools.code_generation")

# ============== MODEL CONFIGURATION ==============

# Code generation model configurations with pricing (per 1M tokens)
# Easy to extend with new models
CODE_GEN_MODELS = {
    "gemini-3-pro-preview": {
        "model_id": "gemini-3-pro-preview",
        "provider": "vertex_ai",
        "thinking_enabled": True,
        "default_thinking_level": "LOW",
        "pricing": {
            "input": 2.00,   # $2.00 per 1M input tokens
            "output": 12.00  # $12.00 per 1M output tokens
        }
    },
    # Future models - add configurations here
    # "claude-opus": {
    #     "model_id": "claude-opus-4",
    #     "provider": "anthropic",
    #     "thinking_enabled": False,
    #     "pricing": {"input": 15.00, "output": 75.00}
    # },
}

DEFAULT_CODE_MODEL = "gemini-3-pro-preview"

# ============== SYSTEM PROMPT ==============

CODE_GENERATION_SYSTEM_PROMPT = """You are an expert software engineer and coding assistant. Your primary focus is helping users with code-related tasks.

## Your Capabilities:
1. **Code Generation**: Write clean, efficient, and well-documented code in any programming language
2. **Code Explanation**: Explain code snippets clearly, breaking down complex logic
3. **Debugging Help**: Identify issues and suggest fixes
4. **Best Practices**: Recommend coding patterns, optimizations, and industry standards
5. **Multi-language Support**: Proficient in Python, JavaScript, TypeScript, Go, Rust, C, C++, Java, Kotlin, Swift, Ruby, PHP, SQL, and more

## Response Guidelines:
- **Be Concise**: Provide direct, actionable answers without unnecessary verbosity
- **Use Code Blocks**: Always wrap code in appropriate markdown code blocks with language specifiers
- **Explain When Asked**: If the user asks for explanation, provide clear step-by-step breakdown
- **Consider Edge Cases**: Mention important edge cases and error handling when relevant
- **Modern Practices**: Use modern language features and current best practices
- **Security Aware**: Point out potential security issues in code when relevant

## Code Style:
- Write readable, self-documenting code
- Use meaningful variable and function names
- Include brief inline comments for complex logic
- Follow language-specific conventions (PEP 8 for Python, etc.)

## When Answering Questions:
- If it's a coding question, provide code examples
- If it's conceptual, give a clear explanation with examples if helpful
- If the question is ambiguous, provide the most likely interpretation and note alternatives

Remember: Quality over quantity. A working, clean solution is better than an over-engineered one."""


# ============== SINGLETON CLIENT ==============

_vertex_client: Optional[genai.Client] = None


def get_vertex_client() -> genai.Client:
    """Get or create singleton Vertex AI client for Gemini 3 Pro."""
    global _vertex_client
    if _vertex_client is None:
        _vertex_client = genai.Client(
            vertexai=True,
            project="effortless-lock-329115",
            location="global"
        )
    return _vertex_client


# ============== CODE GENERATION TOOL ==============

def generate_code(
    query: str,
    model: str = DEFAULT_CODE_MODEL,
    thinking_level: str = "LOW"
) -> str:
    """
    Generate code using a specialized code generation model.

    This tool is designed to be called by the CodeGenerationAgent when users
    request code writing, code explanation, debugging help, or other programming tasks.

    Args:
        query: The user's coding question or request. Should include:
               - What language to use (if specific)
               - What the code should do
               - Any constraints or requirements
        model: The model to use for generation. Options:
               - "gemini-3-pro-preview" (default) - Best for complex code tasks
               - Future: "claude-opus" for alternative perspective
        thinking_level: Thinking depth for Gemini 3 Pro. Options:
                       - "LOW" (default) - Faster, good for simpler tasks
                       - "HIGH" - More thorough reasoning for complex problems

    Returns:
        Generated code with explanations in markdown format.
        The response includes properly formatted code blocks with language tags.

    Example:
        >>> result = generate_code(
        ...     query="Write a Python function to check if a number is prime",
        ...     model="gemini-3-pro-preview",
        ...     thinking_level="LOW"
        ... )
    """
    logger.info(f"[CodeGen Tool] Generating code with model: {model}, thinking: {thinking_level}")
    logger.info(f"[CodeGen Tool] Query: {query[:100]}...")

    try:
        # Validate model
        if model not in CODE_GEN_MODELS:
            logger.warning(f"Unknown model '{model}', falling back to {DEFAULT_CODE_MODEL}")
            model = DEFAULT_CODE_MODEL

        model_config = CODE_GEN_MODELS[model]

        # Build the full prompt
        full_prompt = f"{CODE_GENERATION_SYSTEM_PROMPT}\n\n## User Request:\n{query}"

        # Generate based on provider
        if model_config["provider"] == "vertex_ai":
            client = get_vertex_client()

            # Configure thinking level if supported
            config = None
            if model_config.get("thinking_enabled"):
                config = GenerateContentConfig(
                    thinking_config=ThinkingConfig(thinking_level=thinking_level)
                )

            # Generate response (synchronous for tool use)
            response = client.models.generate_content(
                model=model_config["model_id"],
                contents=full_prompt,
                config=config,
            )

            result = response.text

            # Log token usage if available
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = response.usage_metadata
                input_tokens = getattr(usage, 'prompt_token_count', 0) or 0
                output_tokens = getattr(usage, 'candidates_token_count', 0) or 0
                logger.info(f"[CodeGen Tool] Tokens - Input: {input_tokens}, Output: {output_tokens}")

            logger.info(f"[CodeGen Tool] Generated {len(result)} chars of response")
            return result

        # Future: Add other providers here
        # elif model_config["provider"] == "anthropic":
        #     # Anthropic implementation
        #     pass

        else:
            error_msg = f"Provider '{model_config['provider']}' not yet implemented"
            logger.error(f"[CodeGen Tool] {error_msg}")
            return f"Error: {error_msg}"

    except Exception as e:
        logger.error(f"[CodeGen Tool] Error generating code: {e}", exc_info=True)
        return f"Error generating code: {str(e)}. Please try again or rephrase your request."


def get_available_code_models() -> dict:
    """
    Get information about available code generation models.

    Returns:
        Dict with model information including pricing and capabilities.
    """
    models = []
    for model_id, config in CODE_GEN_MODELS.items():
        models.append({
            "model_id": model_id,
            "provider": config.get("provider", "unknown"),
            "thinking_enabled": config.get("thinking_enabled", False),
            "default_thinking_level": config.get("default_thinking_level", "LOW"),
            "pricing": {
                "input_per_1m_tokens_usd": config.get("pricing", {}).get("input", 0),
                "output_per_1m_tokens_usd": config.get("pricing", {}).get("output", 0),
            }
        })

    return {
        "models": models,
        "default_model": DEFAULT_CODE_MODEL,
        "supported_languages": [
            "Python", "JavaScript", "TypeScript", "Go", "Rust",
            "C", "C++", "Java", "Kotlin", "Swift", "Ruby", "PHP",
            "SQL", "Bash", "HTML/CSS", "and more..."
        ]
    }


# For testing
if __name__ == "__main__":
    # Test the tool
    result = generate_code(
        query="Write a Python function to reverse a linked list",
        model="gemini-3-pro-preview",
        thinking_level="LOW"
    )
    print(result)
