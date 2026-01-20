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
from typing import Optional, Literal, AsyncGenerator, List
from enum import Enum
import json
import asyncio
from google import genai
from google.genai.types import GenerateContentConfig, ThinkingConfig
from src.middleware.auth_middleware import get_current_user, get_user_id_from_token
from src.services.firestore_service import firestore_service
from src.config import Config
from src.logging_config import get_logger

logger = get_logger("chatbot.routes.code_gen")

router = APIRouter(prefix="/api", tags=["code-generation"])


async def balance_exceeded_stream(balance_info: dict) -> AsyncGenerator[str, None]:
    """
    Generate a streaming response when user has exceeded their balance limit.
    """
    error_message = balance_info.get("message", "Monthly limit exceeded. Please recharge to continue.")
    error_data = {
        "type": "balance_exceeded",
        "message": error_message,
        "total_cost_inr": balance_info.get("total_cost_inr", 0),
        "limit_inr": balance_info.get("limit_inr", 100),
        "remaining_balance": balance_info.get("remaining_balance", 0)
    }
    yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
    yield "data: [DONE]\n\n"


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

## What to do if you don't know or user asks about any topic not related to coding:
- Politely inform the user that your expertise is focused on coding and software development. 
- You dont have capacity to answer questions outside this domain. You are only here to help with coding related tasks.
- Also say that kindly use the normal chat session, this chat sssion is dedicated to Coding ONLY ! you can do so by clciking the toggle botton avalable at top right corner for non coding related questions like, news, weather, general knowledge etc.

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

class ConversationMessage(BaseModel):
    """A single message in conversation history."""
    role: Literal["user", "assistant"] = Field(..., description="Message role")
    content: str = Field(..., description="Message content")


class CodeGenRequest(BaseModel):
    """Request model for code generation."""
    query: str = Field(..., description="The user's coding question or request", min_length=1)
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for message logging. If not provided, messages won't be saved to Firestore."
    )
    model: Optional[str] = Field(
        default=DEFAULT_MODEL.value,
        description="Model to use for generation. Default: gemini-3-pro-preview"
    )
    thinking_level: Optional[Literal["LOW", "HIGH"]] = Field(
        default="LOW",
        description="Thinking level for Gemini 3 Pro (LOW or HIGH). Default: LOW"
    )
    conversation_history: Optional[List[ConversationMessage]] = Field(
        default=None,
        description="Previous conversation messages for context"
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
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    conversation_history: Optional[List[ConversationMessage]] = None
) -> AsyncGenerator[str, None]:
    """
    Generate streaming code response using specified model.
    Tracks token usage and updates user cost in Firestore.
    Saves messages to Firestore if session_id is provided.

    Args:
        query: The user's current coding question or request
        model: Model to use for generation
        thinking_level: Thinking level for Gemini 3 Pro
        user_id: Firebase UID for cost tracking
        session_id: Session ID for message logging
        conversation_history: Previous messages for context

    Yields:
        Server-Sent Events (SSE) formatted chunks
    """
    input_tokens = 0
    output_tokens = 0
    final_response = ""  # Store complete response for message logging

    print(f"\n\nGenerating code stream with model: {model}, thinking_level: {thinking_level}")
    print(f"Session ID: {session_id}, User ID: {user_id}")

    try:
        # Generate and send session title for first message
        if user_id and session_id:
            try:
                # Check if this is the first message in the session
                messages = await firestore_service.get_messages(user_id, session_id)
                is_first_message = len(messages) == 0
                
                if is_first_message:
                    logger.info(f"📝 [CodeGen] Generating session title for first message")
                    
                    # Generate a short title using a simple LLM call
                    title_prompt = f"""Generate a very short, concise title (3-5 words maximum) for a code session based on this user query: "{query}"

Examples:
User: "How do I sort a list in Python?"
Answer: Python list sorting

User: "Create a REST API with FastAPI"
Answer: FastAPI REST API

User: "Explain how async/await works"
Answer: Async/await explanation

Now generate ONLY the title for: "{query}"
Answer:"""

                    # Use Gemini to generate title
                    def generate_title_sync():
                        client = genai.Client(
                            vertexai=True,
                            project="effortless-lock-329115",
                            location="global"
                        )
                        response = client.models.generate_content(
                            model="gemini-3-pro-preview",
                            contents=title_prompt
                        )
                        return response

                    # Run in executor to avoid blocking
                    loop = asyncio.get_running_loop()
                    title_response = await loop.run_in_executor(None, generate_title_sync)
                    
                    session_title = title_response.text.strip().strip('"').strip("'")
                    
                    # Remove common prefixes
                    for prefix in ["Title:", "Answer:", "Response:", "Code:"]:
                        if session_title.startswith(prefix):
                            session_title = session_title[len(prefix):].strip()
                            break
                    
                    # Ensure it's not too long
                    if len(session_title.split()) > 5:
                        session_title = ' '.join(session_title.split()[:5])
                    
                    logger.info(f"✅ [CodeGen] Generated session title: {session_title}")
                    
                    # Send session description event as first stream
                    yield f"event: session_description\ndata: {json.dumps({'description': session_title, 'session_id': session_id})}\n\n"
                    
                    # Update session title in Firestore immediately
                    try:
                        success = await firestore_service.update_session_title(
                            user_id=user_id,
                            session_id=session_id,
                            title=session_title
                        )
                        if success:
                            logger.info(f"✅ [CodeGen] Updated session title in Firestore: {session_title}")
                        else:
                            logger.warning(f"⚠️ [CodeGen] Failed to update session title in Firestore")
                    except Exception as title_error:
                        logger.error(f"❌ [CodeGen] Error updating session title: {title_error}")
                        
            except Exception as e:
                logger.error(f"❌ [CodeGen] Failed to generate session title: {e}")
                # Continue without title generation
                pass

        # Build the full prompt with system context and conversation history
        prompt_parts = [CODE_GENERATION_SYSTEM_PROMPT]

        # Add conversation history if provided
        if conversation_history and len(conversation_history) > 0:
            history_text = "\n\n## Previous Conversation:\n"
            for msg in conversation_history:
                role_label = "User" if msg.role == "user" else "Assistant"
                history_text += f"{role_label}: {msg.content}\n\n"
            prompt_parts.append(history_text)

        # Add current user request
        prompt_parts.append(f"\n\n## Current User Request:\n{query}")

        full_prompt = "".join(prompt_parts)

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
                    # Accumulate response for message logging
                    final_response += chunk.text
                    
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

        # Save messages to Firestore in background (non-blocking)
        async def save_code_messages_background():
            """Background task to save code generation messages without blocking the response."""
            try:
                if user_id and session_id:
                    # Save user query
                    await firestore_service.add_message(
                        user_id=user_id,
                        session_id=session_id,
                        role='user',
                        content=query
                    )
                    logger.info(f"💾 [CodeGen] Saved user query to Firestore (session: {session_id})")

                    # Save assistant response
                    await firestore_service.add_message(
                        user_id=user_id,
                        session_id=session_id,
                        role='assistant',
                        content=final_response
                    )
                    logger.info(f"💾 [CodeGen] Saved assistant response to Firestore (session: {session_id})")
            except Exception as save_error:
                logger.error(f"❌ [CodeGen] Failed to save messages to Firestore: {save_error}", exc_info=True)

        # Create background task to save messages (fire and forget)
        if user_id and session_id:
            asyncio.create_task(save_code_messages_background())

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
    Saves messages to Firestore if session_id is provided.

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
    session_id = request.session_id

    # Check user balance before processing request
    balance_info = await firestore_service.check_user_balance(user_id)
    if not balance_info.get("has_balance", True):
        logger.warning(f"[CodeGen] User {user_id} has exceeded monthly limit: ₹{balance_info.get('total_cost_inr', 0):.2f}")
        return StreamingResponse(
            balance_exceeded_stream(balance_info),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    # Create session if session_id is provided but doesn't exist
    if session_id and user_id:
        try:
            existing_session = await firestore_service.get_session(user_id, session_id)
            if not existing_session:
                await firestore_service.create_session(
                    user_id=user_id,
                    session_id=session_id,
                    title="New Code Session",
                    mode="code"
                )
                logger.info(f"✨ [CodeGen] Created new code session: {session_id}")
        except Exception as session_err:
            logger.warning(f"⚠️ [CodeGen] Failed to create session: {session_err}")

    logger.info(f"[CodeGen] Stream request - User: {user_id}, Session: {session_id}")
    logger.info(f"[CodeGen] Model: {request.model}, Thinking: {request.thinking_level}")
    logger.info(f"[CodeGen] Query: {request.query[:100]}...")
    logger.info(f"[CodeGen] Conversation history: {len(request.conversation_history or [])} messages")

    # HARDCODED: Always use Gemini 3 Pro regardless of frontend request
    hardcoded_model = "gemini-3-pro-preview"

    return StreamingResponse(
        generate_code_stream(
            query=request.query,
            model=hardcoded_model,
            thinking_level=request.thinking_level,
            user_id=user_id,
            session_id=session_id,
            conversation_history=request.conversation_history
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
    Message saving is also disabled unless session_id is provided with "test-user" as user_id.
    """
    logger.info(f"[CodeGen-Test] Model: {request.model}, Thinking: {request.thinking_level}")
    logger.info(f"[CodeGen-Test] Query: {request.query[:100]}...")
    logger.info(f"[CodeGen-Test] Session ID: {request.session_id}")

    # HARDCODED: Always use Gemini 3 Pro regardless of frontend request
    hardcoded_model = "gemini-3-pro-preview"

    return StreamingResponse(
        generate_code_stream(
            query=request.query,
            model=hardcoded_model,
            thinking_level=request.thinking_level,
            user_id=None,  # No cost tracking for test endpoint
            session_id=None  # No message saving for test endpoint
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
