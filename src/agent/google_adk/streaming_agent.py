"""Streaming agent implementation for Google ADK multi-agent coordination.

This implementation follows Google ADK best practices:
- Uses runner.run_async() for async iteration over events
- Leverages callbacks for agent/model/tool lifecycle events
- Processes events directly as they stream from the agent
- Implements multi-agent coordination via sub-agents

Supports multiple model providers via LiteLLM:
- Gemini (native): "gemini-2.5-flash"
- OpenAI: "openai/gpt-4o"
- Anthropic: "anthropic/claude-3-5-sonnet-20241022"
- Ollama: "ollama_chat/llama3.2"
"""
import json
import re
import time
import warnings
from typing import List, Dict, AsyncGenerator, Optional
import uuid

# Suppress OpenTelemetry context warnings that occur in async streaming
warnings.filterwarnings("ignore", message=".*was created in a different Context.*")

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .coordinator_agent import create_coordinator_agent
from .callbacks import (
    ADKCallbackHandler,
    StreamingCallbackContext,
    create_streaming_callback_handler
)
from ...config import Config
from ...logging_config import get_logger
from ...utils.token_tracker import get_request_tracker, reset_request_tracker
from ...tools.document_rag import set_current_session_id

logger = get_logger("chatbot.adk_streaming")

# Configuration constants
APP_NAME = "AetherAI_ADK_MultiAgent"
DEFAULT_USER_ID = "user_001"


async def create_adk_streaming_response(
    message: str,
    conversation_history: List[Dict[str, str]],
    session_id: str = None,
    user_id: str = None,
    model_provider: Optional[str] = None,
    response_style: Optional[str] = None,
    tool: Optional[str] = None,
    preference_responses: Optional[List[Dict]] = None
) -> AsyncGenerator[str, None]:
    """
    Create async generator for streaming ADK agent responses with tool execution updates.

    Following Google ADK best practices:
    - Uses runner.run_async() for async event iteration
    - Processes events for text, tool calls, agent transfers
    - Uses callbacks for lifecycle event handling

    Args:
        message: User's message
        conversation_history: List of previous conversation messages
        session_id: Optional session ID for document queries
        user_id: Firebase Auth user ID for user-specific tools
        model_provider: Model provider string, e.g.:
            - "gemini-2.5-flash" (default, native Gemini)
            - "openai/gpt-4o" (OpenAI via LiteLLM)
            - "anthropic/claude-3-5-sonnet-20241022" (Anthropic via LiteLLM)
            - "ollama_chat/llama3.2" (Ollama via LiteLLM)
        response_style: Response style preference
        tool: Optional explicit tool routing (e.g., "shopping_assist" for direct shopping mode)
        preference_responses: List of user preference answers for shopping workflow Phase 2

    Yields:
        SSE-formatted strings with event updates
    """
    try:
        # Reset token tracker for this request
        reset_request_tracker()
        tracker = get_request_tracker()

        # Create streaming context and callback handler
        callback_handler, streaming_context = create_streaming_callback_handler(
            max_tool_calls=Config.MAX_TOOL_CALLS
        )

        # Create coordinator agent with callbacks and model provider
        coordinator_agent = create_coordinator_agent(
            callback_handler=callback_handler,
            streaming_context=streaming_context,
            model_provider=model_provider
        )

        # Initialize session service
        session_service = InMemorySessionService()

        # Generate session ID if not provided
        if session_id is None:
            session_id = f"session_{uuid.uuid4().hex[:8]}"

        if user_id is None:
            user_id = DEFAULT_USER_ID

        # Set session_id in context for tools to access
        set_current_session_id(session_id)

        # Create session with session_id in state for tool access
        await session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
            state={'session_id': session_id, 'user_id': user_id}
        )

        # Create runner
        runner = Runner(
            agent=coordinator_agent,
            app_name=APP_NAME,
            session_service=session_service
        )

        logger.info(f"Starting ADK streaming agent with session: {session_id}")
        logger.info(f"📩 User message: {message}")

        # Build system prompt with response style modifier (if needed for state)
        style_name = response_style or Config.DEFAULT_RESPONSE_STYLE
        if style_name != "Normal":
            logger.info(f"🎨 Using response style: {style_name}")

        # Handle preference responses (Phase 2 of shopping workflow)
        if preference_responses:
            logger.info(f"📋 Received {len(preference_responses)} preference responses - Phase 2: Product Search")
            # Format preference responses into a structured message
            formatted_preferences = []
            for pref in preference_responses:
                # Convert Pydantic model to dict if needed
                if hasattr(pref, 'model_dump'):
                    pref_dict = pref.model_dump()
                elif hasattr(pref, 'dict'):
                    pref_dict = pref.dict()
                else:
                    pref_dict = pref

                question = pref_dict.get('question', '')
                selected = pref_dict.get('options_selected', '')
                # Handle both string and list selections
                if isinstance(selected, list):
                    selected_str = ', '.join(selected)
                else:
                    selected_str = str(selected)
                formatted_preferences.append(f"- {question}: {selected_str}")

            preferences_text = '\n'.join(formatted_preferences)
            final_message = f"""[SHOPPING PREFERENCES COLLECTED - PHASE 2]

User has answered the preference questions. Here are their preferences:
{preferences_text}

NEXT ACTION: Immediately delegate to ProductSearchAgent to search for products matching these preferences.
Then delegate to ProductSummarizationAgent to format the results."""

            # Ensure shopping_assist tool is set for routing
            if not tool:
                tool = "shopping_assist"

            logger.info(f"✅ Formatted preferences for product search")
        else:
            # Handle conditional routing via tool parameter
            final_message = message
            if tool:
                logger.info(f"🎯 Explicit tool routing requested: {tool}")
                if tool == "shopping_assist":
                    # Prepend routing hint to ensure ShoppingAssistAgent is invoked
                    final_message = f"[USER WANTS TO SHOP/BUY PRODUCTS] {message}"
                    logger.info(f"🛍️ Routing to ShoppingAssistAgent")

        # Create the message content
        content = types.Content(
            role='user',
            parts=[types.Part(text=final_message)]
        )

        # Send connected event with session_id
        yield f"event: connected\ndata: {json.dumps({'status': 'connected', 'session_id': session_id})}\n\n"

        # Send initial thinking event
        yield f"event: thinking\ndata: {json.dumps({'status': 'Thinking...'})}\n\n"

        # Map tool names to display names with emojis
        tool_display_names = {
            'calculator': '🧮 Calculating',
            'google_search_with_context': '🌐 Searching the web',
            'get_current_datetime_ist': '🕐 Getting current time',
            'query_documents': '📄 Analyzing documents',
            'fetch_gmail_messages': '📧 Fetching news from emails',
            'gmail_auth_status': '🔐 Checking Gmail auth status',
            'fetch_url_content': '🔗 Fetching URL content',
            'fetch_multiple_urls': '🔗 Fetching multiple URLs',
            'search_nearby_places': '📍 Searching nearby places',
            'get_directions': '🗺️ Getting directions',
            'get_traffic_info': '🚗 Checking traffic',
            'get_place_details': '🏪 Getting place details',
            'explore_area': '🔍 Exploring area',
            'transfer_to_agent': '🔄 Delegating to specialist'
        }

        # Track state
        complete_response = ""
        tool_count = 0
        last_heartbeat = time.time()
        maps_widget_data = None
        current_agent = "CoordinatorAgent"

        # Stream events using run_async (ADK pattern)
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content
        ):
            # Check for pending events from callbacks
            for cb_event in streaming_context.get_pending_events():
                event_type = cb_event['event_type']
                event_data = cb_event['data']
                yield f"event: {event_type}\ndata: {json.dumps(event_data)}\n\n"

            # Handle event based on type
            author = getattr(event, 'author', None)
            
            # Track agent changes
            if author and author != 'user' and author != current_agent:
                current_agent = author
                logger.info(f"🔄 Agent taking control: {current_agent}")
                yield f"event: thinking\ndata: {json.dumps({'status': f'{current_agent} working...'})}\n\n"

            # Check for function calls (tool requests)
            function_calls = event.get_function_calls() if hasattr(event, 'get_function_calls') else []
            if function_calls:
                for call in function_calls:
                    tool_name = call.name
                    tool_count += 1
                    display_name = tool_display_names.get(tool_name, f'🔧 {tool_name}')
                    
                    # Check if it's an agent transfer
                    if tool_name == 'transfer_to_agent':
                        target_agent = call.args.get('agent_name', 'specialist')
                        logger.info(f"🔀 Handoff requested to: {target_agent}")
                        yield f"event: thinking\ndata: {json.dumps({'status': f'Handing off to {target_agent}'})}\n\n"
                    else:
                        tool_data = {
                            'status': display_name,
                            'tool_name': tool_name,
                            'display_name': display_name,
                            'tool_count': tool_count,
                            'max_tools': Config.MAX_TOOL_CALLS
                        }
                        yield f"event: tool\ndata: {json.dumps(tool_data)}\n\n"
                        logger.info(f"🔧 Tool #{tool_count}/{Config.MAX_TOOL_CALLS}: {display_name}")

            # Check for function responses (tool results)
            function_responses = event.get_function_responses() if hasattr(event, 'get_function_responses') else []
            if function_responses:
                for response in function_responses:
                    tool_name = response.name
                    result = response.response
                    
                    # Check for maps widget data in response
                    if isinstance(result, dict):
                        result_str = json.dumps(result)
                        if '<!--MAPS_WIDGET:' in result_str:
                            match = re.search(r'<!--MAPS_WIDGET:(.*?)-->', result_str, re.DOTALL)
                            if match:
                                try:
                                    maps_widget_data = json.loads(match.group(1))
                                    logger.info(f"📍 Captured maps widget data")
                                except json.JSONDecodeError:
                                    pass

            # Handle text content
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_chunk = part.text
                        
                        # Check if this is partial/streaming text
                        is_partial = getattr(event, 'partial', False)
                        
                        if is_partial:
                            # Stream partial text immediately
                            complete_response += text_chunk
                            yield f"event: message\ndata: {json.dumps({'chunk': text_chunk})}\n\n"
                        else:
                            # For final/complete messages
                            if event.is_final_response():
                                complete_response += text_chunk
                                yield f"event: message\ndata: {json.dumps({'chunk': text_chunk})}\n\n"

            # Check for agent transfer actions
            if hasattr(event, 'actions') and event.actions:
                if hasattr(event.actions, 'transfer_to_agent') and event.actions.transfer_to_agent:
                    target_agent = event.actions.transfer_to_agent
                    logger.info(f"🔀 Transferring to: {target_agent}")
                    yield f"event: thinking\ndata: {json.dumps({'status': f'Delegating to {target_agent}'})}\n\n"

            # Send periodic heartbeat to keep connection alive
            if time.time() - last_heartbeat > 15:
                yield ": heartbeat\n\n"
                last_heartbeat = time.time()

        # Get token usage from streaming context (if tracked)
        input_tokens = 0
        output_tokens = 0
        
        # Calculate cost for this request
        model_id = Config.GEMINI_MODEL_ID
        cost_data = tracker.calculate_cost(model_id=model_id)
        
        logger.info("=" * 80)
        logger.info(f"📊 TOKEN USAGE SUMMARY")
        logger.info(f"Model: {model_id}")
        logger.info(f"Input Tokens:  {cost_data['input_tokens']:,}")
        logger.info(f"Output Tokens: {cost_data['output_tokens']:,}")
        logger.info(f"Total Tokens:  {cost_data['total_tokens']:,}")
        logger.info(f"💰 Cost: ₹{cost_data['total_cost_inr']:.4f} (${cost_data['total_cost_usd']:.6f})")
        logger.info("=" * 80)

        # Append maps widget metadata to response if captured
        final_response = complete_response
        if maps_widget_data:
            logger.info(f"📍 Appending maps widget metadata to response")
            final_response += f"\n\n<!--MAPS_WIDGET:{json.dumps(maps_widget_data)}-->"
        elif streaming_context.maps_widget_data:
            logger.info(f"📍 Appending maps widget metadata from context")
            final_response += f"\n\n<!--MAPS_WIDGET:{json.dumps(streaming_context.maps_widget_data)}-->"

        # Send completion event with full response and cost
        completion_data = {
            'status': 'Done!' if tool_count == 0 else f'Done! (used {tool_count} tool{"s" if tool_count > 1 else ""})',
            'response': final_response,
            'session_id': session_id,
            'tool_count': tool_count,
            'cost_inr': cost_data['total_cost_inr'],
            'cost_usd': cost_data['total_cost_usd'],
            'tokens': {
                'input': cost_data['input_tokens'],
                'output': cost_data['output_tokens'],
                'total': cost_data['total_tokens']
            }
        }
        yield f"event: done\ndata: {json.dumps(completion_data)}\n\n"
        logger.info(f"✅ ADK Streaming completed. Tools used: {tool_count}")
        logger.info(f"📝 Response: {complete_response[:200]}...")

    except Exception as e:
        logger.error(f"ADK Streaming error: {str(e)}", exc_info=True)
        error_data = {
            'error': str(e),
            'type': type(e).__name__
        }
        yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
