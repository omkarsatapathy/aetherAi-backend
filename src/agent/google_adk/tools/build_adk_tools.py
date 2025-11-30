"""Build ADK tools by wrapping tool functions in FunctionTool.

This module creates FunctionTool wrappers for all tools used by ADK agents.
FunctionTool is the standard way to expose Python functions to Google ADK agents.
"""
from google.adk.tools import FunctionTool

# Import all tool functions from the main tools package
from ....tools.gmail import fetch_gmail_messages, gmail_auth_status
from ....tools.google_search import google_search_with_context
from ....tools.image_analysis import analyze_image
from ....tools.google_maps import (
    search_nearby_places,
    get_directions,
    get_traffic_info,
    get_place_details,
    explore_area
)
from ....tools.document_rag import query_documents
from ....tools.link_executor import fetch_url_content, fetch_multiple_urls
from ....tools.datetime_ist import get_current_datetime_ist


# ====================
# Gmail Tools
# ====================
gmail_messages_tool = FunctionTool(func=fetch_gmail_messages)
gmail_auth_tool = FunctionTool(func=gmail_auth_status)


# ====================
# Search Tools
# ====================
google_search_tool = FunctionTool(func=google_search_with_context)


# ====================
# URL/Link Tools
# ====================
fetch_url_content_tool = FunctionTool(func=fetch_url_content)
fetch_multiple_urls_tool = FunctionTool(func=fetch_multiple_urls)


# ====================
# Google Maps Tools
# ====================
search_nearby_places_tool = FunctionTool(func=search_nearby_places)
get_directions_tool = FunctionTool(func=get_directions)
get_traffic_info_tool = FunctionTool(func=get_traffic_info)
get_place_details_tool = FunctionTool(func=get_place_details)
explore_area_tool = FunctionTool(func=explore_area)


# ====================
# Document/RAG Tools
# ====================
query_documents_tool = FunctionTool(func=query_documents)


# ====================
# Utility Tools
# ====================
datetime_ist_tool = FunctionTool(func=get_current_datetime_ist)


# ====================
# Image Analysis Tools
# ====================
image_analysis_tool = FunctionTool(func=analyze_image)


# Export all wrapped tools
__all__ = [
    # Gmail
    'gmail_messages_tool',
    'gmail_auth_tool',
    # Search
    'google_search_tool',
    # URL
    'fetch_url_content_tool',
    'fetch_multiple_urls_tool',
    # Maps
    'search_nearby_places_tool',
    'get_directions_tool',
    'get_traffic_info_tool',
    'get_place_details_tool',
    'explore_area_tool',
    # Documents
    'query_documents_tool',
    # Utility
    'datetime_ist_tool',
    # Image
    'image_analysis_tool',
]
