"""Gmail tool for fetching emails - Multi-tenant secure version."""
import base64
import json
from typing import Dict
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from .auth_manager import GmailAuthManager
from ..config import Config
from ..logging_config import get_logger
from strands import tool

logger = get_logger("chatbot.gmail.tool")


def _clean_email_text(text: str) -> str:
    """Clean up email text by removing extra whitespace and formatting."""
    import re
    # Replace multiple newlines with double newline
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Replace non-breaking spaces
    text = text.replace('\xa0', ' ')
    # Remove lines that are just whitespace
    lines = [line.rstrip() for line in text.split('\n')]
    text = '\n'.join(line for line in lines if line.strip() or line == '')
    # Remove excessive spaces
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def _get_email_body(payload: Dict) -> str:
    """Extract email body from message payload."""
    body = ""

    # Try to get text/plain first (cleaner than HTML)
    if 'parts' in payload:
        for part in payload['parts']:
            # Handle nested multipart
            if 'parts' in part:
                body = _get_email_body(part)
                if body:
                    return body
            # Get text/plain
            if part['mimeType'] == 'text/plain' and 'data' in part.get('body', {}):
                body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                return body

        # Fall back to text/html if no plain text
        for part in payload['parts']:
            if part['mimeType'] == 'text/html' and 'data' in part.get('body', {}):
                body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                return body

    # Single part message
    elif 'data' in payload.get('body', {}):
        body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
        return body

    return ""


@tool
def fetch_gmail_messages(
    user_id: str,
    max_results: int = None,
    query: str = ""
) -> str:
    """
    Strands tool: Fetch the most recent Gmail messages from inbox for authenticated user.

    SECURITY: This function requires user_id from Firebase Auth. The user_id must be
    extracted from the authenticated session - NEVER accept it from user input.

    Fetches emails from the inbox and sorts them by receive time (newest first) using Gmail's internalDate.
    Includes all inbox emails (Primary, Promotions, Social, Updates tabs).

    Args:
        user_id: Firebase Auth user ID (from authenticated session - REQUIRED)
        max_results: Maximum number of messages to fetch (default 15)
        query: Optional Gmail search query for filtering (e.g., "is:unread", "from:example@gmail.com", "newer_than:7d", "category:primary")

    Returns:
        JSON string containing list of messages with id, subject, from, date, snippet, and full body content, sorted newest first
    """
    max_results = max_results or Config.GMAIL_DEFAULT_MAX_RESULTS
    auth_manager = GmailAuthManager()

    logger.info("Starting Gmail message fetch", extra={"extra_data": {
        "max_results": max_results, "query": query, "user_id": user_id
    }})

    # Check if user is authenticated
    if not auth_manager.is_authenticated(user_id):
        logger.warning(f"User {user_id} not authenticated for Gmail")
        return json.dumps({
            "error": "Not authenticated",
            "message": "Please authenticate with Gmail first. Visit the account settings to authorize Gmail access.",
            "auth_required": True
        })

    try:
        # Get user-specific credentials
        credentials = auth_manager.get_credentials(user_id)

        if not credentials:
            logger.error(f"Failed to retrieve credentials for user {user_id}")
            return json.dumps({
                "error": "Credentials unavailable",
                "message": "Unable to retrieve Gmail credentials. Please re-authorize.",
                "auth_required": True
            })

        # Build Gmail service with user's credentials
        service = build('gmail', 'v1', credentials=credentials)
        max_results = min(max_results, Config.GMAIL_MAX_RESULTS_LIMIT)

        logger.debug(f"Fetching messages from Gmail API for user {user_id}")

        # Fetch from INBOX
        results = service.users().messages().list(
            userId='me',
            maxResults=max_results,
            labelIds=['INBOX'],
            q=query
        ).execute()
        messages = results.get('messages', [])

        if not messages:
            logger.info(f"No messages found for user {user_id}")
            return json.dumps({"messages": [], "count": 0, "message": "No messages found matching the query."})

        # Fetch detailed message data with internalDate for sorting
        detailed_messages = []
        for msg in messages:
            try:
                msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
                headers = msg_data['payload']['headers']
                body = _get_email_body(msg_data['payload'])

                # Clean up the body text
                if body:
                    body = _clean_email_text(body)

                if len(body) > Config.GMAIL_BODY_MAX_LENGTH:
                    body = body[:Config.GMAIL_BODY_MAX_LENGTH] + "... [truncated]"

                message_info = {
                    'id': msg_data['id'],
                    'subject': next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject'),
                    'from': next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown'),
                    'date': next((h['value'] for h in headers if h['name'].lower() == 'date'), 'Unknown'),
                    'snippet': msg_data.get('snippet', ''),
                    'internalDate': int(msg_data.get('internalDate', 0))  # Store for sorting
                }

                if body:
                    message_info['body'] = body
                detailed_messages.append(message_info)
            except HttpError as e:
                logger.warning(f"Failed to fetch message {msg['id']}: {str(e)}")
                continue

        # Sort messages by internalDate (newest first)
        detailed_messages.sort(key=lambda x: x.get('internalDate', 0), reverse=True)

        # Remove internalDate from response
        for msg in detailed_messages:
            msg.pop('internalDate', None)

        logger.info(f"Successfully fetched {len(detailed_messages)} Gmail messages for user {user_id}",
            extra={"extra_data": {"count": len(detailed_messages), "query": query}})

        return json.dumps({"messages": detailed_messages, "count": len(detailed_messages), "query": query}, ensure_ascii=False)

    except HttpError as e:
        logger.error(f"Gmail API error for user {user_id}", extra={"extra_data": {"error": str(e)}}, exc_info=True)
        return json.dumps({"error": "Gmail API error", "message": f"Failed to fetch messages: {str(e)}"})
    except Exception as e:
        logger.error(f"Unexpected error fetching Gmail messages for user {user_id}", extra={"extra_data": {"error": str(e)}}, exc_info=True)
        return json.dumps({"error": "Unexpected error", "message": f"Failed to fetch messages: {str(e)}"})


@tool
def gmail_auth_status(user_id: str) -> str:
    """
    Strands tool: Check Gmail authentication status for user.

    SECURITY: This function requires user_id from Firebase Auth. The user_id must be
    extracted from the authenticated session - NEVER accept it from user input.

    Args:
        user_id: Firebase Auth user ID (from authenticated session - REQUIRED)

    Returns:
        JSON string with authentication status
    """
    auth_manager = GmailAuthManager()
    status = auth_manager.get_auth_status(user_id)

    logger.info("Gmail auth status checked", extra={"extra_data": {
        "user_id": user_id, "is_authenticated": status['authenticated']
    }})

    return json.dumps(status)
