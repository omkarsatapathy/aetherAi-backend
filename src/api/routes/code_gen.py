"""Code Generation endpoint - Streaming LLM response for code generation and explanation.

Supports multiple models:
- gemini-3-pro-preview (default) - Google's Gemini 3 Pro with thinking capabilities
- claude-sonnet (future)
- claude-opus (future)

Features:
- Streaming responses for real-time output
- Optimized system prompt for code generation
- Multi-language support (Python, JavaScript, TypeScript, Go, Rust, C, C++, Java, etc.)
- Code explanation and Q&A capabilities
- Firebase authentication with token/cost tracking
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Literal, AsyncGenerator
from enum import Enum
import json
from google import genai
from google.genai.types import GenerateContentConfig, ThinkingConfig
from src.middleware.auth_middleware import get_current_user, get_user_id_from_token
from src.services.firestore_service import firestore_service
from src.config import Config
from src.logging_config import get_logger

logger = get_logger("chatbot.routes.code_gen")

router = APIRouter(prefix="/api", tags=["code-generation"])

# ============== MODEL CONFIGURATION ==============

class ModelProvider(str, Enum):
    """Supported model providers for code generation."""
    GEMINI_3_PRO = "gemini-3-pro-preview"
    # Future providers (placeholder for extensibility)
    # CLAUDE_SONNET = "claude-sonnet"
    # CLAUDE_OPUS = "claude-opus"


# Model configurations with pricing (per 1M tokens)
MODEL_CONFIG = {
    ModelProvider.GEMINI_3_PRO: {
        "model_id": "gemini-3-pro-preview",
        "provider": "vertex_ai",
        "thinking_enabled": True,
        "default_thinking_level": "LOW",
        # Pricing from Config.LLM_PRICING for gemini-3-pro
        "pricing": {
            "input": 2.00,   # $2.00 per 1M input tokens
            "output": 12.00  # $12.00 per 1M output tokens
        }
    },
    # Future: Add Claude configurations here
}

DEFAULT_MODEL = ModelProvider.GEMINI_3_PRO

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


# ============== REQUEST/RESPONSE MODELS ==============

class CodeGenRequest(BaseModel):
    """Request model for code generation."""
    query: str = Field(..., description="The user's coding question or request", min_length=1)
    model: Optional[str] = Field(
        default=DEFAULT_MODEL.value,
        description="Model to use for generation. Default: gemini-3-pro-preview"
    )
    thinking_level: Optional[Literal["LOW", "HIGH"]] = Field(
        default="LOW",
        description="Thinking level for Gemini 3 Pro (LOW or HIGH). Default: LOW"
    )

    class Config:
        extra = 'ignore'


class CodeGenResponse(BaseModel):
    """Response model for non-streaming code generation."""
    response: str
    model_used: str
    usage: Optional[dict] = None

    class Config:
        extra = 'ignore'


# ============== COST CALCULATION ==============

def calculate_code_gen_cost(input_tokens: int, output_tokens: int, model: str = DEFAULT_MODEL.value) -> dict:
    """
    Calculate cost for code generation request.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model used for generation

    Returns:
        Dict with cost breakdown in USD and INR
    """
    # Get pricing for the model
    model_enum = ModelProvider(model) if model in [m.value for m in ModelProvider] else DEFAULT_MODEL
    pricing = MODEL_CONFIG.get(model_enum, {}).get("pricing", {"input": 2.00, "output": 12.00})

    # Calculate base costs (per 1M tokens)
    input_cost_usd = (input_tokens / 1_000_000) * pricing["input"]
    output_cost_usd = (output_tokens / 1_000_000) * pricing["output"]

    # Add API overhead (40% as per Config)
    total_cost_usd = (input_cost_usd + output_cost_usd) * (1 + Config.API_OVERHEAD_PERCENTAGE)
    total_cost_inr = total_cost_usd * Config.USD_TO_INR

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "input_cost_usd": round(input_cost_usd, 6),
        "output_cost_usd": round(output_cost_usd, 6),
        "total_cost_usd": round(total_cost_usd, 6),
        "total_cost_inr": round(total_cost_inr, 4),
        "model": model
    }


# ============== STREAMING GENERATOR ==============

async def generate_code_stream(
    query: str,
    model: str = DEFAULT_MODEL.value,
    thinking_level: str = "LOW",
    user_id: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Generate streaming code response using specified model.
    Tracks token usage and updates user cost in Firestore.

    Yields:
        Server-Sent Events (SSE) formatted chunks
    """
    input_tokens = 0
    output_tokens = 0

    print(f"\n\nGenerating code stream with model: {model}, thinking_level: {thinking_level}")

    try:
        # Build the full prompt with system context
        full_prompt = f"{CODE_GENERATION_SYSTEM_PROMPT}\n\n## User Request:\n{query}"

        if model == ModelProvider.GEMINI_3_PRO.value:
            client = get_vertex_client()

            config = GenerateContentConfig(
                thinking_config=ThinkingConfig(thinking_level=thinking_level)
            )

            # Estimate input tokens (rough: ~4 chars per token)
            input_tokens = len(full_prompt) // 4

            # Use synchronous streaming (genai SDK streaming is sync)
            for chunk in client.models.generate_content_stream(
                model=model,
                contents=full_prompt,
                config=config,
            ):
                if chunk.text:
                    # Estimate output tokens from chunk
                    output_tokens += len(chunk.text) // 4
                    # Format as SSE - JSON encode to preserve newlines
                    yield f"data: {json.dumps(chunk.text)}\n\n"

                # Try to get actual usage from chunk if available
                if hasattr(chunk, 'usage_metadata') and chunk.usage_metadata:
                    if hasattr(chunk.usage_metadata, 'prompt_token_count') and chunk.usage_metadata.prompt_token_count is not None:
                        input_tokens = chunk.usage_metadata.prompt_token_count
                    if hasattr(chunk.usage_metadata, 'candidates_token_count') and chunk.usage_metadata.candidates_token_count is not None:
                        output_tokens = chunk.usage_metadata.candidates_token_count

        # Future: Add Claude model support here
        # elif model in [ModelProvider.CLAUDE_SONNET.value, ModelProvider.CLAUDE_OPUS.value]:
        #     # Anthropic streaming implementation
        #     pass

        else:
            error_msg = f"Error: Unsupported model '{model}'"
            yield f"data: {json.dumps(error_msg)}\n\n"
            return

        # Calculate and track costs
        cost_data = calculate_code_gen_cost(input_tokens, output_tokens, model)

        # Update user cost in Firestore (if authenticated)
        if user_id:
            try:
                await firestore_service.update_user_cost(
                    user_id=user_id,
                    cost_inr=cost_data["total_cost_inr"],
                    cost_usd=cost_data["total_cost_usd"],
                    input_tokens=input_tokens,
                    output_tokens=output_tokens
                )
                logger.info(
                    f"💰 [CodeGen] User {user_id} - Tokens: {input_tokens}+{output_tokens}, "
                    f"Cost: ₹{cost_data['total_cost_inr']:.4f}"
                )
            except Exception as cost_err:
                logger.warning(f"Failed to update user cost: {cost_err}")

        # Send usage metadata before completion
        usage_json = f'{{"input_tokens":{input_tokens},"output_tokens":{output_tokens},"total_cost_inr":{cost_data["total_cost_inr"]:.4f}}}'
        yield f"data: [USAGE]{usage_json}[/USAGE]\n\n"

        # Send completion signal
        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.error(f"❌ Error in code generation stream: {e}", exc_info=True)
        yield f"data: [ERROR] Error generating code: {str(e)}\n\n"


# ============== ENDPOINTS ==============

@router.post("/code/stream")
async def code_gen_stream(
    request: CodeGenRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Stream code generation responses.

    Requires Firebase Authentication.
    Tracks token usage and costs per user.

    **Supported Models:**
    - `gemini-3-pro-preview` (default) - Google's Gemini 3 Pro with thinking capabilities

    **Coming Soon:**
    - `claude-sonnet` - Anthropic's Claude Sonnet
    - `claude-opus` - Anthropic's Claude Opus

    **Thinking Levels (Gemini 3 Pro only):**
    - `LOW` (default) - Faster responses, suitable for simpler queries
    - `HIGH` - More thorough reasoning, better for complex tasks

    **Cost:** ~$2/1M input tokens, ~$12/1M output tokens + 40% API overhead
    """
    user_id = get_user_id_from_token(current_user)

    logger.info(f"[CodeGen] Stream request - User: {user_id}")
    logger.info(f"[CodeGen] Model: {request.model}, Thinking: {request.thinking_level}")
    logger.info(f"[CodeGen] Query: {request.query[:100]}...")

    return StreamingResponse(
        generate_code_stream(
            query=request.query,
            model=request.model,
            thinking_level=request.thinking_level,
            user_id=user_id
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/code/stream/test")
async def code_gen_stream_test(request: CodeGenRequest):
    """
    Test streaming endpoint (NO AUTH REQUIRED - for development only).

    Remove this endpoint in production!

    Note: Cost tracking is disabled for test endpoint.
    """
    logger.info(f"[CodeGen-Test] Model: {request.model}, Thinking: {request.thinking_level}")
    logger.info(f"[CodeGen-Test] Query: {request.query[:100]}...")

    return StreamingResponse(
        generate_code_stream(
            query=request.query,
            model=request.model,
            thinking_level=request.thinking_level,
            user_id=None  # No cost tracking for test endpoint
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/code/models")
async def get_available_models():
    """
    Get available models for code generation.

    Returns list of supported models with their configurations and pricing.
    """
    models = []
    for provider in ModelProvider:
        config = MODEL_CONFIG.get(provider, {})
        pricing = config.get("pricing", {})
        models.append({
            "model_id": provider.value,
            "provider": config.get("provider", "unknown"),
            "thinking_enabled": config.get("thinking_enabled", False),
            "default_thinking_level": config.get("default_thinking_level", "LOW"),
            "available": provider == ModelProvider.GEMINI_3_PRO,  # Only Gemini available for now
            "pricing": {
                "input_per_1m_tokens_usd": pricing.get("input", 0),
                "output_per_1m_tokens_usd": pricing.get("output", 0),
                "api_overhead_percentage": Config.API_OVERHEAD_PERCENTAGE * 100
            }
        })

    return {
        "models": models,
        "default_model": DEFAULT_MODEL.value,
        "default_thinking_level": "LOW",
        "supported_languages": [
            "Python", "JavaScript", "TypeScript", "Go", "Rust",
            "C", "C++", "Java", "Kotlin", "Swift", "Ruby", "PHP",
            "SQL", "Bash", "HTML/CSS", "and more..."
        ]
    }


@router.get("/code/cost")
async def get_user_code_cost(current_user: dict = Depends(get_current_user)):
    """
    Get current user's code generation cost tracking data.

    Returns cumulative costs for the current billing cycle (30 days).
    """
    user_id = get_user_id_from_token(current_user)

    cost_data = await firestore_service.get_user_cost(user_id)

    if not cost_data:
        return {
            "total_cost_inr": 0,
            "total_cost_usd": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "days_remaining": 30,
            "message": "No usage recorded yet"
        }

    return cost_data
