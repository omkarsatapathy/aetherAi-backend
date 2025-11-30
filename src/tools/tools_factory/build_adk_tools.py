"""Build ADK tools by wrapping tool functions in FunctionTool."""
from google.adk.tools import FunctionTool

# Import all tool functions
from ..gmail import fetch_gmail_messages, gmail_auth_status
from ..google_search import google_search_with_context
from ..image_analysis import analyze_image
from ..google_maps import (
    search_nearby_places,
    get_directions,
    get_traffic_info,
    get_place_details,
    explore_area
)
from ..document_rag import query_documents
from ..link_executor import fetch_url_content, fetch_multiple_urls
from ..datetime_ist import get_current_datetime_ist

# Wrap all tools in FunctionTool
gmail_messages_tool = FunctionTool(func=fetch_gmail_messages)
gmail_auth_tool = FunctionTool(func=gmail_auth_status)
google_search_tool = FunctionTool(func=google_search_with_context)
image_analysis_tool = FunctionTool(func=analyze_image)
search_nearby_places_tool = FunctionTool(func=search_nearby_places)
get_directions_tool = FunctionTool(func=get_directions)
get_traffic_info_tool = FunctionTool(func=get_traffic_info)
get_place_details_tool = FunctionTool(func=get_place_details)
explore_area_tool = FunctionTool(func=explore_area)
query_documents_tool = FunctionTool(func=query_documents)
fetch_url_content_tool = FunctionTool(func=fetch_url_content)
fetch_multiple_urls_tool = FunctionTool(func=fetch_multiple_urls)
datetime_ist_tool = FunctionTool(func=get_current_datetime_ist)

# Export all wrapped tools
__all__ = [
    'gmail_messages_tool',
    'gmail_auth_tool',
    'google_search_tool',
    'image_analysis_tool',
    'search_nearby_places_tool',
    'get_directions_tool',
    'get_traffic_info_tool',
    'get_place_details_tool',
    'explore_area_tool',
    'query_documents_tool',
    'fetch_url_content_tool',
    'fetch_multiple_urls_tool',
    'datetime_ist_tool'
]
