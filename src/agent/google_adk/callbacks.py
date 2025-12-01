"""ADK Callbacks for agent lifecycle, LLM interaction, and tool execution.

This module implements callbacks for Google ADK agents following the official
callback patterns documented at https://google.github.io/adk-docs/callbacks/

Callbacks provide hooks to:
- Observe, customize, and control agent behavior
- Implement guardrails and validation
- Track tool usage and enforce limits
- Stream events to frontend

Types of Callbacks:
- Agent Lifecycle: before_agent_callback, after_agent_callback
- LLM Interaction: before_model_callback, after_model_callback
- Tool Execution: before_tool_callback, after_tool_callback
"""
import json
import time
from typing import Optional, Dict, Any, Callable, AsyncGenerator
from dataclasses import dataclass, field
from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from ...logging_config import get_logger

logger = get_logger("chatbot.adk_callbacks")


@dataclass
class StreamingCallbackContext:
    """
    Context for streaming callbacks that tracks state across callback invocations.
    
    This is used to accumulate data for SSE streaming to the frontend.
    """
    tool_count: int = 0
    max_tool_calls: int = 20
    complete_response: str = ""
    maps_widget_data: Optional[Dict] = None
    last_heartbeat: float = field(default_factory=time.time)
    current_agent: str = ""
    events_queue: list = field(default_factory=list)
    
    def add_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Add an event to be streamed to the frontend."""
        self.events_queue.append({
            'event_type': event_type,
            'data': data,
            'timestamp': time.time()
        })
    
    def get_pending_events(self) -> list:
        """Get and clear pending events."""
        events = self.events_queue.copy()
        self.events_queue.clear()
        return events
    
    def should_send_heartbeat(self, interval: float = 15.0) -> bool:
        """Check if a heartbeat should be sent."""
        if time.time() - self.last_heartbeat > interval:
            self.last_heartbeat = time.time()
            return True
        return False


class ToolLimitCallback:
    """
    Callback to limit tool calls and prevent infinite loops.
    
    Similar to ToolLimitHook in Strands, this uses ADK's before_tool_callback
    to enforce a maximum number of tool calls.
    """
    
    def __init__(self, max_calls: int = 50, context: Optional[StreamingCallbackContext] = None):
        """
        Initialize the tool limit callback.
        
        Args:
            max_calls: Maximum number of tool calls allowed
            context: Optional streaming context to update
        """
        self.max_calls = max_calls
        self.context = context or StreamingCallbackContext(max_tool_calls=max_calls)
        logger.info(f"ToolLimitCallback initialized with max_calls={max_calls}")
    
    def before_tool_callback(
        self,
        tool: BaseTool,
        args: Dict[str, Any],
        tool_context: ToolContext
    ) -> Optional[Dict]:
        """
        Called before each tool execution.
        
        Args:
            tool: The BaseTool instance being called
            args: Arguments passed to the tool
            tool_context: ToolContext with session state and tool info
            
        Returns:
            None to proceed, or a dict to skip tool execution and return this result
        """
        tool_name = tool.name if hasattr(tool, 'name') else str(tool)
        self.context.tool_count += 1
        
        logger.info(f"🔧 Tool call #{self.context.tool_count}/{self.max_calls}: {tool_name}")
        logger.debug(f"   Args: {json.dumps(args, default=str)[:200]}")
        
        # Add event for frontend
        self.context.add_event('tool', {
            'status': f'Using {tool_name}',
            'tool_name': tool_name,
            'tool_count': self.context.tool_count,
            'max_tools': self.max_calls
        })
        
        # Check if limit exceeded
        if self.context.tool_count > self.max_calls:
            logger.warning(f"⛔ Tool call limit exceeded! Canceling tool: {tool_name}")
            return {
                'error': f'Maximum tool call limit of {self.max_calls} reached.',
                'message': 'Please provide your final answer based on the information gathered.'
            }
        
        return None  # Proceed with tool execution
    
    def after_tool_callback(
        self,
        tool: BaseTool,
        args: Dict[str, Any],
        tool_context: ToolContext,
        tool_response: Dict
    ) -> Optional[Dict]:
        """
        Called after each tool execution.
        
        Args:
            tool: The BaseTool instance that was called
            args: Arguments passed to the tool
            tool_context: ToolContext with session state and tool info
            tool_response: Result returned by the tool
            
        Returns:
            None to use original response, or dict to replace the response
        """
        tool_name = tool.name if hasattr(tool, 'name') else str(tool)
        logger.info(f"✅ Tool completed: {tool_name}")
        
        # Check for maps widget data in response
        if isinstance(tool_response, dict):
            response_str = json.dumps(tool_response)
            if '<!--MAPS_WIDGET:' in response_str:
                import re
                match = re.search(r'<!--MAPS_WIDGET:(.*?)-->', response_str, re.DOTALL)
                if match:
                    try:
                        self.context.maps_widget_data = json.loads(match.group(1))
                        logger.info(f"📍 Captured maps widget data")
                    except json.JSONDecodeError:
                        pass
        
        return None  # Use original response


class ADKCallbackHandler:
    """
    Comprehensive callback handler for ADK agents.
    
    This class provides all callback types for agent lifecycle, LLM interaction,
    and tool execution. It supports streaming events to the frontend via SSE.
    """
    
    # Map tool names to display names with emojis
    TOOL_DISPLAY_NAMES = {
        # 'calculator': 'Calculating',
        'google_search_with_context': 'Searching',
        # 'get_current_datetime_ist': 'Getting current time',
        'query_documents': 'Analyzing documents',
        # 'query_documents_wrapper': 'Analyzing documents',
        'fetch_gmail_messages': 'Fetching news from emails',
        # 'fetch_gmail_wrapper': 'Fetching news from emails',
        'gmail_auth_status': 'Authenticating',
        # 'gmail_auth_wrapper': 'Checking Gmail auth status',
        'fetch_url_content': 'Fetching content ',
        'fetch_multiple_urls': 'Fetching multiple URLs',
        'search_nearby_places': 'Searching nearby places',
        'get_directions': 'Getting directions',
        'get_traffic_info': 'Checking traffic',
        # 'get_place_details': 'Getting place details',
        # 'explore_area': 'Exploring area'
    }
    
    def __init__(
        self,
        max_tool_calls: int = 50,
        streaming_context: Optional[StreamingCallbackContext] = None
    ):
        """
        Initialize the ADK callback handler.
        
        Args:
            max_tool_calls: Maximum number of tool calls allowed
            streaming_context: Optional context for streaming events
        """
        self.context = streaming_context or StreamingCallbackContext(max_tool_calls=max_tool_calls)
        self.tool_limit = ToolLimitCallback(max_tool_calls, self.context)
        logger.info(f"ADKCallbackHandler initialized with max_tool_calls={max_tool_calls}")
    
    # ==================== Agent Lifecycle Callbacks ====================
    
    def before_agent_callback(
        self,
        callback_context: Any,  # CallbackContext from ADK
    ) -> Optional[types.Content]:
        """
        Called before agent's main execution logic starts.
        
        Use this to:
        - Set up resources for the agent's run
        - Perform validation checks on session state
        - Log entry point of agent activity
        - Potentially skip agent execution by returning Content
        
        Args:
            callback_context: ADK CallbackContext with session state and invocation details
            
        Returns:
            None to proceed with agent execution, or Content to skip and return directly
        """
        # Get agent name from context if available
        agent_name = getattr(callback_context, 'agent_name', 'Agent')
        self.context.current_agent = agent_name
        
        logger.info(f"🔄 Agent starting: {agent_name}")
        
        # Add event for frontend
        self.context.add_event('thinking', {
            'status': f'{agent_name} working...'
        })
        
        return None  # Proceed with agent execution
    
    def after_agent_callback(
        self,
        callback_context: Any,
    ) -> Optional[types.Content]:
        """
        Called after agent's main execution completes.
        
        Use this to:
        - Perform cleanup tasks
        - Post-execution validation
        - Log completion of agent activity
        - Modify or replace agent's output
        
        Args:
            callback_context: ADK CallbackContext
            
        Returns:
            None to use agent's output, or Content to replace it
        """
        agent_name = getattr(callback_context, 'agent_name', None) or self.context.current_agent or 'Agent'
        logger.info(f"✅ Agent completed: {agent_name}")
        
        return None  # Use original output
    
    # ==================== LLM Interaction Callbacks ====================
    
    def before_model_callback(
        self,
        callback_context: Any,
        llm_request: Any  # LlmRequest from ADK
    ) -> Optional[Any]:  # LlmResponse
        """
        Called before sending request to the LLM.
        
        Use this to:
        - Inspect or modify the request going to the LLM
        - Add dynamic instructions
        - Implement input guardrails
        - Implement request-level caching
        
        Args:
            callback_context: ADK CallbackContext
            llm_request: The request about to be sent to the LLM
            
        Returns:
            None to proceed with LLM call, or LlmResponse to skip LLM and use this response
        """
        logger.debug(f"📤 Sending request to LLM")
        
        # Add thinking event
        self.context.add_event('thinking', {
            'status': 'Thinking...'
        })
        
        return None  # Proceed with LLM call
    
    def after_model_callback(
        self,
        callback_context: Any,
        llm_response: Any  # LlmResponse from ADK
    ) -> Optional[Any]:  # LlmResponse
        """
        Called after receiving response from the LLM.
        
        Use this to:
        - Log model outputs
        - Reformat responses
        - Censor sensitive information
        - Parse structured data and store in state
        
        Args:
            callback_context: ADK CallbackContext
            llm_response: The response received from the LLM
            
        Returns:
            None to use original response, or LlmResponse to replace it
        """
        logger.debug(f"📥 Received response from LLM")
        
        # Extract and accumulate text from response
        if hasattr(llm_response, 'content') and llm_response.content:
            content = llm_response.content
            if hasattr(content, 'parts') and content.parts:
                for part in content.parts:
                    if hasattr(part, 'text') and part.text:
                        # Add text event for streaming
                        self.context.add_event('message', {
                            'chunk': part.text
                        })
        
        return None  # Use original response
    
    # ==================== Tool Execution Callbacks ====================
    
    def before_tool_callback(
        self,
        tool: BaseTool,
        args: Dict[str, Any],
        tool_context: ToolContext
    ) -> Optional[Dict]:
        """
        Called before a tool is executed.
        
        Use this to:
        - Inspect and modify tool arguments
        - Perform authorization checks
        - Log tool usage attempts
        - Implement tool-level caching
        - Skip tool execution by returning a result dict
        
        Args:
            tool: The BaseTool instance being called
            args: Arguments to be passed to the tool
            tool_context: ToolContext with session state and tool info
            
        Returns:
            None to proceed with tool execution, or dict to skip and use this as result
        """
        tool_name = tool.name if hasattr(tool, 'name') else str(tool)
        
        # Use tool limit callback
        result = self.tool_limit.before_tool_callback(tool, args, tool_context)
        
        if result is None:
            # Get display name for the tool
            display_name = self.TOOL_DISPLAY_NAMES.get(tool_name, f'🔧 {tool_name}')
            
            # Add tool event for frontend
            self.context.add_event('tool', {
                'status': display_name,
                'tool_name': tool_name,
                'display_name': display_name,
                'tool_count': self.context.tool_count,
                'max_tools': self.context.max_tool_calls
            })
        
        return result
    
    def after_tool_callback(
        self,
        tool: BaseTool,
        args: Dict[str, Any],
        tool_context: ToolContext,
        tool_response: Dict
    ) -> Optional[Dict]:
        """
        Called after a tool execution completes.
        
        Use this to:
        - Log tool results
        - Post-process or format results
        - Save specific parts to session state
        - Replace the tool result
        
        Args:
            tool: The BaseTool instance that was called
            args: Arguments passed to the tool
            tool_context: ToolContext with session state and tool info
            tool_response: Result returned by the tool
            
        Returns:
            None to use original response, or dict to replace it
        """
        return self.tool_limit.after_tool_callback(tool, args, tool_context, tool_response)
    
    def get_callbacks_dict(self) -> Dict[str, Callable]:
        """
        Get a dictionary of all callbacks for passing to LlmAgent.
        
        Returns:
            Dictionary mapping callback names to callback functions
        """
        return {
            'before_agent_callback': self.before_agent_callback,
            'after_agent_callback': self.after_agent_callback,
            'before_model_callback': self.before_model_callback,
            'after_model_callback': self.after_model_callback,
            'before_tool_callback': self.before_tool_callback,
            'after_tool_callback': self.after_tool_callback,
        }


def create_streaming_callback_handler(
    max_tool_calls: int = 20
) -> tuple[ADKCallbackHandler, StreamingCallbackContext]:
    """
    Create a callback handler and context for streaming responses.
    
    Args:
        max_tool_calls: Maximum number of tool calls allowed
        
    Returns:
        Tuple of (ADKCallbackHandler, StreamingCallbackContext)
    """
    context = StreamingCallbackContext(max_tool_calls=max_tool_calls)
    handler = ADKCallbackHandler(max_tool_calls=max_tool_calls, streaming_context=context)
    return handler, context
