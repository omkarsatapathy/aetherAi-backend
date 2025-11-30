"""Tool wrapper functions for session-specific and global tools."""
from typing import Optional, List
from strands import tool
from ..config import Config
from ..gmail.tool import fetch_gmail_messages, gmail_auth_status
from ..tools.document_rag import query_documents


def get_session_tools(session_id: str, user_id: str = None) -> List:
    """Get tools with session context (Gmail + Documents).

    Args:
        session_id: Session ID for document queries
        user_id: Firebase Auth user ID for user-specific tools

    Returns:
        List of configured tools
    """
    def fetch_gmail_wrapper(query: str = "") -> dict:
        """Fetch the most recent Gmail messages from inbox.

        This tool fetches up to 15 most recent emails from the inbox (includes all tabs: Primary, Promotions, Social, Updates).
        Messages are sorted by receive time (newest first).
        Use query parameter for filtering (e.g., "is:unread", "category:primary", "from:example@gmail.com", "newer_than:7d").

        Args:
            query: Optional Gmail search query for filtering (default: "" for all messages)

        Returns:
            Dictionary containing list of messages with id, subject, from, date, snippet, and full body, sorted newest first
        """
        return fetch_gmail_messages(
            user_id=user_id,
            max_results=Config.GMAIL_DEFAULT_MAX_RESULTS,
            query=query
        )

    def gmail_auth_wrapper() -> dict:
        """Check Gmail authentication status.

        Returns:
            Dictionary with authentication status
        """
        return gmail_auth_status(user_id=user_id)

    def query_documents_wrapper(query: str) -> dict:
        """Query uploaded documents for information using RAG.

        Use this tool when the user asks questions about their uploaded documents.

        Args:
            query: The question about the documents

        Returns:
            Dictionary with answer from documents
        """
        return query_documents(query=query, session_id=session_id)

    return [
        tool(fetch_gmail_wrapper),
        tool(gmail_auth_wrapper),
        tool(query_documents_wrapper)
    ]


def get_gmail_tools(user_id: str = None) -> List:
    """Get Gmail tools without session context.

    Args:
        user_id: Firebase Auth user ID for user-specific tools

    Returns:
        List of Gmail tools
    """
    def fetch_gmail_wrapper(query: str = "") -> dict:
        """Fetch the most recent Gmail messages from inbox.

        This tool fetches up to 15 most recent emails from the inbox (includes all tabs: Primary, Promotions, Social, Updates).
        Messages are sorted by receive time (newest first).
        Use query parameter for filtering (e.g., "is:unread", "category:primary", "from:example@gmail.com", "newer_than:7d").

        Args:
            query: Optional Gmail search query for filtering (default: "" for all messages)

        Returns:
            Dictionary containing list of messages with id, subject, from, date, snippet, and full body, sorted newest first
        """
        return fetch_gmail_messages(
            user_id=user_id,
            max_results=Config.GMAIL_DEFAULT_MAX_RESULTS,
            query=query
        )

    def gmail_auth_wrapper() -> dict:
        """Check Gmail authentication status."""
        return gmail_auth_status(user_id=user_id)

    return [
        tool(fetch_gmail_wrapper),
        tool(gmail_auth_wrapper)
    ]
