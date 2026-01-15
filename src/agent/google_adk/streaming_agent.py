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
from ...utils.json_structure_enforcer import get_json_enforcer
from ...tools.document_rag import set_current_session_id
from ...tools.google_maps import set_current_session_id as set_maps_session_id, LocationRequiredException
from ...services.firestore_service import firestore_service
import asyncio

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
        set_maps_session_id(session_id)

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

        # Fetch user persona for message enrichment
        user_persona = None
        persona_context = ""
        if user_id:
            try:
                user_persona = await firestore_service.get_user_persona(user_id)
                if user_persona:
                    logger.info(f"📋 User persona loaded for {user_id}: {user_persona}")
                    # Build persona context for agent (invisible to user)
                    gender = user_persona.get('gender', 'Unknown')
                    age_group = user_persona.get('ageGroup', 'Unknown')
                    country = user_persona.get('country', 'Unknown')
                    ethnicities = user_persona.get('ethnicities', [])
                    ethnicities_str = ', '.join(ethnicities) if ethnicities else 'Not specified'

                    persona_context = f"""[INTERNAL USER CONTEXT - DO NOT MENTION IN RESPONSE]
User Profile: {gender}, {age_group}, from {country}
Cultural Background: {ethnicities_str}
[END INTERNAL CONTEXT]

"""
                else:
                    logger.debug(f"📋 No persona found for user {user_id}")
            except Exception as persona_error:
                logger.warning(f"Failed to fetch user persona: {persona_error}")

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
            final_message = f"""{persona_context}[SHOPPING PREFERENCES COLLECTED - PHASE 2]

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
            # Prepend persona context to enrich the message
            final_message = f"{persona_context}{message}" if persona_context else message
            if tool:
                logger.info(f"🎯 Explicit tool routing requested: {tool}")
                if tool == "shopping_assist":
                    # Prepend routing hint to ensure ShoppingAssistAgent is invoked
                    final_message = f"{persona_context}[USER WANTS TO SHOP/BUY PRODUCTS] {message}"
                    logger.info(f"🛍️ Routing to ShoppingAssistAgent")

        # Log the enriched message for debugging
        if persona_context:
            logger.info(f"🔄 Enriched message with persona context (first 200 chars): {final_message[:200]}...")

        # Create the message content
        content = types.Content(
            role='user',
            parts=[types.Part(text=final_message)]
        )

        # Send connected event with session_id
        yield f"event: connected\ndata: {json.dumps({'status': 'connected', 'session_id': session_id})}\n\n"

        # Generate session description for first message
        # Check if this is the first message by looking at conversation_history length
        # The frontend sends the current message in history, so we check if it's <= 1
        is_first_message = len(conversation_history) <= 1

        if is_first_message:
            logger.info(f"📝 Generating session description for first message")
            try:
                # Generate a short 3-5 word description using a simple LLM call
                description_prompt = f"""Generate a very short, concise title (3-5 words maximum) for a chat session based on this user message: "{message}"

Examples:
User: "What's the weather like today?"
Answer: Weather inquiry

User: "Help me find a good laptop under $1000"
Answer: Laptop shopping

User: "Explain quantum physics to me"
Answer: Quantum physics explanation

Now generate ONLY the title for: "{message}"
Answer:"""

                # Use the model to generate description (run in executor to avoid blocking)
                from google import genai

                def generate_title_sync():
                    client = genai.Client(api_key=Config.GEMINI_API_KEY)
                    response = client.models.generate_content(
                        model=Config.GEMINI_MODEL_ID,
                        contents=description_prompt
                    )
                    return response

                # Run the sync call in a thread pool to avoid blocking
                loop = asyncio.get_running_loop()
                description_response = await loop.run_in_executor(None, generate_title_sync)

                session_description = description_response.text.strip().strip('"').strip("'")

                # Remove common prefixes like "Title:", "Answer:", etc.
                for prefix in ["Title:", "Answer:", "Response:", "Chat:"]:
                    if session_description.startswith(prefix):
                        session_description = session_description[len(prefix):].strip()
                        break

                # Ensure it's not too long
                if len(session_description.split()) > 5:
                    session_description = ' '.join(session_description.split()[:5])

                logger.info(f"✅ Generated session description: {session_description}")

                # Send session description event as first stream
                yield f"event: session_description\ndata: {json.dumps({'description': session_description, 'session_id': session_id})}\n\n"

                # Update session title in Firestore immediately
                if user_id and session_id:
                    try:
                        success = await firestore_service.update_session_title(
                            user_id=user_id,
                            session_id=session_id,
                            title=session_description
                        )
                        if success:
                            logger.info(f"✅ Updated session title in Firestore: {session_description}")
                        else:
                            logger.warning(f"⚠️ Failed to update session title in Firestore")
                    except Exception as title_error:
                        logger.error(f"Error updating session title: {title_error}")
            except Exception as e:
                logger.error(f"Failed to generate session description: {e}")
                # Continue without description
                pass

        # Send initial thinking event
        yield f"event: thinking\ndata: {json.dumps({'status': 'Thinking...'})}\n\n"

        # Map tool names to display names with emojis
        tool_display_names = {
            'calculator': 'Calculating',
            'google_search_with_context': 'Searching the web',
            # 'get_current_datetime_ist': 'Getting current time',
            'query_documents': 'Analyzing documents',
            'fetch_gmail_messages': 'Fetching news from emails',
            'gmail_auth_status': 'Checking Gmail auth status',
            'fetch_url_content': 'Fetching URL content',
            'fetch_multiple_urls': 'Fetching multiple URLs',
            'search_nearby_places': 'Researching nearby places',
            'get_directions': 'Getting directions',
            'get_traffic_info': 'Checking traffic',
            'get_place_details': 'Getting place details',
            'explore_area': 'Exploring area',
            'transfer_to_agent': 'Delegating to specialist',
            # Weather tools
            'get_hourly_forecast': 'Getting hourly forecast',
            'get_tomorrow_forecast': 'Getting tomorrow\'s forecast',
            'get_five_day_forecast': 'Getting 5-day forecast',
            # Location
            'get_location_name': 'Getting your location'
        }

        # Track state
        complete_response = ""
        tool_count = 0
        last_heartbeat = time.time()
        maps_widget_data = None
        current_agent = "CoordinatorAgent"
        location_required = False  # Flag to track if location was requested
        total_input_tokens = 0
        total_output_tokens = 0

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

                    # Debug logging to see what we're getting
                    logger.info(f"🔍 Tool response - Name: {tool_name}, Type: {type(result)}, Value: {str(result)[:200]}")

                    # Check for location request marker (string or dict with 'result' key)
                    is_location_required = False
                    if isinstance(result, str) and result == "LOCATION_REQUIRED":
                        is_location_required = True
                    elif isinstance(result, dict) and result.get('result') == "LOCATION_REQUIRED":
                        is_location_required = True
                    elif isinstance(result, dict) and result.get('output') == "LOCATION_REQUIRED":
                        is_location_required = True

                    if is_location_required:
                        logger.info(f"📍 Location required for {tool_name}, sending location_request event")
                        location_required = True  # Set flag to stop processing

                        # Determine message based on tool name
                        if 'weather' in tool_name.lower() or 'forecast' in tool_name.lower():
                            location_message = 'Location access needed for weather forecast'
                        else:
                            location_message = 'Location access needed for this feature'

                        location_event_data = {
                            'message': location_message,
                            'tool_name': tool_name,
                            'session_id': session_id
                        }
                        yield f"event: location_request\ndata: {json.dumps(location_event_data)}\n\n"

                        # Set a user-friendly response message
                        complete_response = f"I need your location to provide weather information. Please grant location access when prompted."

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

            # Capture token usage from Gemini usage_metadata
            if hasattr(event, 'usage_metadata') and event.usage_metadata:
                usage = event.usage_metadata
                input_tokens = getattr(usage, 'prompt_token_count', 0) or 0
                output_tokens = getattr(usage, 'candidates_token_count', 0) or 0
                if input_tokens > 0:
                    total_input_tokens = input_tokens  # Use latest cumulative value
                if output_tokens > 0:
                    total_output_tokens = output_tokens  # Use latest cumulative value

            # Send periodic heartbeat to keep connection alive
            if time.time() - last_heartbeat > 15:
                yield ": heartbeat\n\n"
                last_heartbeat = time.time()

            # Break the loop if location was required - we need user input first
            if location_required:
                logger.info("📍 Breaking event loop - waiting for user location")
                break

        # Add captured Gemini token usage to the tracker
        if total_input_tokens > 0 or total_output_tokens > 0:
            tracker.add_completion_usage({
                'prompt_tokens': total_input_tokens,
                'completion_tokens': total_output_tokens
            }, model_id=Config.GEMINI_MODEL_ID)

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

        # Update user's cumulative cost in Firestore and get updated monthly total
        # Apply API overhead percentage (e.g., 40% for API services on top of LLM cost)
        monthly_cost_data = None
        if user_id and (cost_data['total_cost_inr'] > 0 or cost_data['input_tokens'] > 0):
            api_multiplier = 1 + Config.API_OVERHEAD_PERCENTAGE  # e.g., 1.40 for 40% overhead
            total_cost_inr_with_api = cost_data['total_cost_inr'] * api_multiplier
            total_cost_usd_with_api = cost_data['total_cost_usd'] * api_multiplier

            logger.info(f"💵 API overhead applied: {Config.API_OVERHEAD_PERCENTAGE * 100:.0f}% | "
                       f"LLM: ₹{cost_data['total_cost_inr']:.4f} → Total: ₹{total_cost_inr_with_api:.4f}")

            try:
                # Update cost and get the new monthly total (synchronously to include in response)
                monthly_cost_data = await firestore_service.update_user_cost(
                    user_id=user_id,
                    cost_inr=total_cost_inr_with_api,
                    cost_usd=total_cost_usd_with_api,
                    input_tokens=cost_data['input_tokens'],
                    output_tokens=cost_data['output_tokens']
                )
                if monthly_cost_data:
                    logger.info(f"💰 Monthly cost updated: ₹{monthly_cost_data.get('total_cost_inr', 0):.4f}")
            except Exception as cost_error:
                logger.error(f"Failed to update user cost: {cost_error}", exc_info=True)

        # Append maps widget metadata to response if captured
        final_response = complete_response
        if maps_widget_data:
            logger.info(f"📍 Appending maps widget metadata to response")
            final_response += f"\n\n<!--MAPS_WIDGET:{json.dumps(maps_widget_data)}-->"
        elif streaming_context.maps_widget_data:
            logger.info(f"📍 Appending maps widget metadata from context")
            final_response += f"\n\n<!--MAPS_WIDGET:{json.dumps(streaming_context.maps_widget_data)}-->"

        # Post-process response to ensure structured JSON output for shopping agents
        # This layer uses LLM to enforce proper JSON structure without changing events
        # IMPORTANT: Only validates/cleans the response, doesn't change event flow
        question_data = None
        product_data = None

        json_enforcer = get_json_enforcer()

        # Extract all JSON blocks from the response
        all_json_blocks = re.findall(r'```json\s*(\{.*?\})\s*```', final_response, re.DOTALL)

        logger.info(f"📊 Found {len(all_json_blocks)} JSON blocks in response")

        # Priority: products > questions (products are the final output of shopping flow)
        # Try to find products JSON first
        for idx, json_block in enumerate(all_json_blocks):
            try:
                parsed = json.loads(json_block)
                if 'products' in parsed and isinstance(parsed['products'], list) and len(parsed['products']) > 0:
                    logger.info(f"🔍 Block {idx+1}: Detected 'products' JSON with {len(parsed['products'])} products - validating")
                    # Validate and enforce structure if needed
                    validated = json_enforcer.extract_product_summary_json(json_block)
                    if validated:
                        product_data = validated
                        logger.info(f"✅ Product JSON validated successfully")
                        # Found valid products, stop looking
                        break
            except Exception as e:
                logger.debug(f"Block {idx+1}: Not valid products JSON - {e}")
                continue

        # If no products found, look for questions JSON
        if not product_data:
            for idx, json_block in enumerate(all_json_blocks):
                try:
                    parsed = json.loads(json_block)
                    if 'questions' in parsed and isinstance(parsed['questions'], list) and len(parsed['questions']) > 0:
                        logger.info(f"🔍 Block {idx+1}: Detected 'questions' JSON with {len(parsed['questions'])} questions - validating")
                        # Validate and enforce structure if needed
                        validated = json_enforcer.extract_shopping_preference_json(json_block)
                        if validated:
                            question_data = validated
                            logger.info(f"✅ Questions JSON validated successfully")
                            # Found valid questions, stop looking
                            break
                except Exception as e:
                    logger.debug(f"Block {idx+1}: Not valid questions JSON - {e}")
                    continue

        # Replace final_response with ONLY the validated JSON (highest priority found)
        # This removes any duplicate or conflicting JSON blocks
        if product_data:
            logger.info("📝 Using validated product JSON as final response")
            intro_message = "Based on your preferences, here are my top recommendations:"
            final_response = f"{intro_message}\n\n```json\n{json.dumps(product_data, indent=2)}\n```"
        elif question_data:
            logger.info("📝 Using validated questions JSON as final response")
            final_response = f"{question_data.get('agent_message', '')}\n\n```json\n{json.dumps(question_data, indent=2)}\n```"
        else:
            # No structured JSON found - leave response as is
            logger.info("ℹ️ No structured JSON detected, keeping original response")

        # Send completion event with full response and cost
        # Determine status based on whether location was required
        if location_required:
            status_msg = 'Waiting for location access'
        elif tool_count == 0:
            status_msg = 'Done!'
        else:
            status_msg = f'Done! (used {tool_count} tool{"s" if tool_count > 1 else ""})'

        completion_data = {
            'status': status_msg,
            'response': final_response,
            'session_id': session_id,
            'tool_count': tool_count,
            'cost_inr': cost_data['total_cost_inr'],
            'cost_usd': cost_data['total_cost_usd'],
            'tokens': {
                'input': cost_data['input_tokens'],
                'output': cost_data['output_tokens'],
                'total': cost_data['total_tokens']
            },
            'location_required': location_required  # Add flag for frontend
        }

        # Add monthly cost data to completion event
        if monthly_cost_data:
            completion_data['monthly_cost'] = {
                'total_cost_inr': monthly_cost_data.get('total_cost_inr', 0),
                'total_cost_usd': monthly_cost_data.get('total_cost_usd', 0),
                'total_input_tokens': monthly_cost_data.get('total_input_tokens', 0),
                'total_output_tokens': monthly_cost_data.get('total_output_tokens', 0),
                'days_remaining': monthly_cost_data.get('days_remaining', 30)
            }

        # Add question field if questions were detected
        if question_data:
            completion_data['question'] = question_data
            logger.info(f"✅ Added 'question' field to completion data")

        # Add products field if product data was detected
        if product_data:
            completion_data['products'] = product_data.get('products', [])
            logger.info(f"✅ Added 'products' field to completion data with {len(completion_data['products'])} products")

        # Save messages to Firestore in background (non-blocking)
        # This happens BEFORE sending the done event so it doesn't block the response
        async def save_messages_background(has_questions: bool = False, skip_save: bool = False):
            """Background task to save messages without blocking the response.

            Args:
                has_questions: If True, skips saving assistant message (preference questions)
                skip_save: If True, skips saving both messages (e.g., location request pending)
            """
            try:
                if skip_save:
                    logger.info(f"⏭️ Skipping message save - location access pending (session: {session_id})")
                    return

                if user_id and session_id:
                    # Save user message
                    await firestore_service.add_message(
                        user_id=user_id,
                        session_id=session_id,
                        role='user',
                        content=message
                    )
                    logger.info(f"💾 Saved user message to Firestore (session: {session_id})")

                    # Save assistant response (skip if it contains preference questions)
                    if has_questions:
                        logger.info(f"⏭️ Skipping assistant message save - contains preference questions (session: {session_id})")
                    else:
                        await firestore_service.add_message(
                            user_id=user_id,
                            session_id=session_id,
                            role='assistant',
                            content=final_response
                        )
                        logger.info(f"💾 Saved assistant response to Firestore (session: {session_id})")

                    # Session title is now updated at the beginning of the conversation
                    # (See session_description event generation above)
            except Exception as save_error:
                logger.error(f"Failed to save messages to Firestore: {save_error}", exc_info=True)

        # Create background task (fire and forget)
        # Pass question_data existence to skip saving preference questions
        # Skip saving entirely if location was required (we'll save when user provides location)
        asyncio.create_task(save_messages_background(
            has_questions=bool(question_data),
            skip_save=location_required
        ))

        # Send done event immediately without waiting for save
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
