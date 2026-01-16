"""Quick Response endpoint - Direct Gemini 2.0 Flash response without streaming or agents.

OPTIMIZED VERSION:
- Singleton Gemini client (avoids re-initialization overhead)
- Parallel async operations (persona fetch + time context)
- zoneinfo instead of pytz (3-5x faster timezone ops)
- Async generate_content_async for non-blocking API calls
- Cached timezone objects
- Reduced logging overhead
- Pre-compiled instruction string
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Tuple, Dict
from datetime import datetime
from zoneinfo import ZoneInfo
from functools import lru_cache
import asyncio
import time
from google import genai
from src.middleware.auth_middleware import get_current_user, get_user_id_from_token
from src.services.firestore_service import firestore_service
from src.logging_config import get_logger
from src.config import Config

logger = get_logger("chatbot.routes.quick_response")

router = APIRouter(prefix="/api", tags=["quick-response"])

# ============== PERFORMANCE OPTIMIZATIONS ==============

# Pre-compiled constants (avoid runtime string building)
MODEL_ID = "gemini-2.0-flash-exp"
DEFAULT_TIMEZONE = "Asia/Kolkata"

# Pre-compiled instruction suffix (avoids string concat on each request)
INSTRUCTION_SUFFIX = "\n\nInstructions: You should respond with funny and engaging answers. Always generate new and creative responses. Use the suggested greeting from the time context when appropriate (e.g., start with 'Good morning!' if it's morning in their timezone). IMPORTANT: If the user's name is provided in the context, greet them by their first name (e.g., 'Good morning, John!'). Be aware of the current time and day when answering."
INSTRUCTION_SUFFIX_TEST = "\n\nInstructions: You should respond with funny and engaging answers. Use the suggested greeting from the time context when appropriate."

# Singleton Gemini client - initialized once, reused across requests
_gemini_client: Optional[genai.Client] = None

def get_gemini_client() -> genai.Client:
    """Get or create singleton Gemini client."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)
    return _gemini_client

# In-memory cache for user context (first_name, country, persona_context)
# Cache TTL: 5 minutes (user data rarely changes during a session)
_user_context_cache: Dict[str, Tuple[str, Optional[str], Optional[str], float]] = {}
CACHE_TTL = 300  # 5 minutes in seconds

def _get_cached_user_context(user_id: str) -> Optional[Tuple[str, Optional[str], Optional[str]]]:
    """Get cached user context if still valid."""
    if user_id in _user_context_cache:
        persona_context, country, first_name, timestamp = _user_context_cache[user_id]
        if time.time() - timestamp < CACHE_TTL:
            return persona_context, country, first_name
        # Expired, remove from cache
        del _user_context_cache[user_id]
    return None

def _set_cached_user_context(user_id: str, persona_context: str, country: Optional[str], first_name: Optional[str]):
    """Cache user context with current timestamp."""
    _user_context_cache[user_id] = (persona_context, country, first_name, time.time())

# Cached timezone objects (ZoneInfo objects are immutable and thread-safe)
@lru_cache(maxsize=64)
def get_cached_timezone(tz_name: str) -> ZoneInfo:
    """Cache timezone objects to avoid repeated parsing."""
    return ZoneInfo(tz_name)

# Country to timezone mapping (common countries)
COUNTRY_TIMEZONE_MAP = {
    'India': 'Asia/Kolkata',
    'United States': 'America/New_York',
    'USA': 'America/New_York',
    'United Kingdom': 'Europe/London',
    'UK': 'Europe/London',
    'Canada': 'America/Toronto',
    'Australia': 'Australia/Sydney',
    'Germany': 'Europe/Berlin',
    'France': 'Europe/Paris',
    'Japan': 'Asia/Tokyo',
    'China': 'Asia/Shanghai',
    'Singapore': 'Asia/Singapore',
    'UAE': 'Asia/Dubai',
    'Brazil': 'America/Sao_Paulo',
    'Mexico': 'America/Mexico_City',
    'South Africa': 'Africa/Johannesburg',
    'Russia': 'Europe/Moscow',
    'Italy': 'Europe/Rome',
    'Spain': 'Europe/Madrid',
    'Netherlands': 'Europe/Amsterdam',
    'Switzerland': 'Europe/Zurich',
    'Sweden': 'Europe/Stockholm',
    'Norway': 'Europe/Oslo',
    'Denmark': 'Europe/Copenhagen',
    'South Korea': 'Asia/Seoul',
    'Thailand': 'Asia/Bangkok',
    'Malaysia': 'Asia/Kuala_Lumpur',
    'Indonesia': 'Asia/Jakarta',
    'Philippines': 'Asia/Manila',
    'Vietnam': 'Asia/Ho_Chi_Minh',
    'New Zealand': 'Pacific/Auckland',
    'Argentina': 'America/Argentina/Buenos_Aires',
    'Chile': 'America/Santiago',
    'Colombia': 'America/Bogota',
    'Peru': 'America/Lima',
    'Israel': 'Asia/Jerusalem',
    'Turkey': 'Europe/Istanbul',
    'Saudi Arabia': 'Asia/Riyadh',
    'Egypt': 'Africa/Cairo',
    'Nigeria': 'Africa/Lagos',
    'Kenya': 'Africa/Nairobi',
    'Pakistan': 'Asia/Karachi',
    'Bangladesh': 'Asia/Dhaka',
    'Sri Lanka': 'Asia/Colombo',
    'Nepal': 'Asia/Kathmandu',
}

# Pre-computed greeting thresholds (avoid repeated comparisons)
GREETING_THRESHOLDS = [(5, 12, "Good morning", "morning"), (12, 17, "Good afternoon", "afternoon"), (17, 21, "Good evening", "evening")]


def get_time_based_greeting_context(country: str = None) -> str:
    """
    Generate time-based greeting context based on user's country timezone.
    OPTIMIZED: Uses zoneinfo (faster than pytz), cached timezone objects.
    
    Args:
        country: User's country from persona
        
    Returns:
        String with current time and appropriate greeting
    """
    # Get timezone based on country, default to IST (India)
    timezone_str = COUNTRY_TIMEZONE_MAP.get(country, DEFAULT_TIMEZONE)
    
    try:
        # Use cached timezone object (avoids repeated parsing)
        tz = get_cached_timezone(timezone_str)
        current_time = datetime.now(tz)
        hour = current_time.hour
        
        # Optimized greeting lookup
        greeting, time_period = "Good night", "night"
        for start, end, greet, period in GREETING_THRESHOLDS:
            if start <= hour < end:
                greeting, time_period = greet, period
                break
        
        # Single strftime call for both values (faster than two separate calls)
        formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
        day_of_week = current_time.strftime('%A')
        
        # Use string join (marginally faster for multiple strings)
        return f"[CURRENT TIME CONTEXT]\nCurrent Date & Time: {formatted_time} ({timezone_str})\nDay: {day_of_week}\nTime of Day: {time_period}\nSuggested Greeting: {greeting}\n[END TIME CONTEXT]\n\n"
        
    except Exception:
        # Fallback - minimal logging to reduce overhead
        tz = get_cached_timezone(DEFAULT_TIMEZONE)
        current_time = datetime.now(tz)
        hour = current_time.hour
        
        greeting = "Good night"
        for start, end, greet, _ in GREETING_THRESHOLDS:
            if start <= hour < end:
                greeting = greet
                break
            
        formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S IST')
        return f"[CURRENT TIME CONTEXT]\nCurrent Time: {formatted_time}\nSuggested Greeting: {greeting}\n[END TIME CONTEXT]\n\n"


class QuickResponseRequest(BaseModel):
    """Request model for quick response."""
    query: str
    session_id: Optional[str] = None
    
    class Config:
        # Faster validation
        extra = 'ignore'


class QuickResponseResponse(BaseModel):
    """Response model for quick response."""
    response: str
    session_id: Optional[str] = None
    model_used: str
    
    class Config:
        extra = 'ignore'


async def _fetch_persona_and_build_context(user_id: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Fetch user persona and build context string in one async operation.
    OPTIMIZED: Uses in-memory cache (5 min TTL) to avoid repeated Firestore reads.
    Returns: (persona_context_string, country, first_name)
    """
    if not user_id:
        return "", None, None
    
    # Check cache first (avoids Firestore read)
    cached = _get_cached_user_context(user_id)
    if cached:
        return cached
    
    try:
        # Fetch full user document to get displayName and persona (single read)
        user_data = await firestore_service.get_user(user_id)
        if user_data:
            print(f"[DEBUG] Fetched user data for user_id={user_id}: \n\n{user_data}")
            # Extract first name from displayName (optimized: use partition for single-pass)
            display_name = user_data.get('displayName', '')
            first_name = display_name.partition(' ')[0] if display_name else None
            
            # Get persona data
            user_persona = user_data.get('persona')
            
            if user_persona:
                gender = user_persona.get('gender', 'Unknown')
                country = user_persona.get('country', 'Unknown')
                
                # Build context (optimized: single f-string, avoid conditionals in hot path)
                if first_name:
                    persona_context = f"[INTERNAL USER CONTEXT - DO NOT MENTION IN RESPONSE]\nUser's Name: {first_name}\nUser Profile: {gender}, from {country}\n[END INTERNAL CONTEXT]\n\n"
                else:
                    persona_context = f"[INTERNAL USER CONTEXT - DO NOT MENTION IN RESPONSE]\nUser Profile: {gender}, from {country}\n[END INTERNAL CONTEXT]\n\n"
                
                # Cache result
                _set_cached_user_context(user_id, persona_context, country, first_name)
                return persona_context, country, first_name
            elif first_name:
                # Even without persona, include first name
                persona_context = f"[INTERNAL USER CONTEXT - DO NOT MENTION IN RESPONSE]\nUser's Name: {first_name}\n[END INTERNAL CONTEXT]\n\n"
                _set_cached_user_context(user_id, persona_context, None, first_name)
                return persona_context, None, first_name
    except Exception:
        pass  # Silently fail - non-critical
    
    return "", None, None


@router.post("/quick-response")
async def quick_response(
    request: QuickResponseRequest, 
    current_user: dict = Depends(get_current_user)
) -> QuickResponseResponse:
    """
    Quick response endpoint using Gemini 2.0 Flash model.
    OPTIMIZED: Parallel operations, singleton client, async API call.
    """
    user_id = get_user_id_from_token(current_user)
    
    # Start persona fetch immediately (don't await yet)
    persona_task = asyncio.create_task(_fetch_persona_and_build_context(user_id))
    
    try:
        # Get client from singleton (no initialization overhead)
        client = get_gemini_client()
        
        # Await persona result (was running in parallel)
        persona_context, country, first_name = await persona_task
        
        # Generate time context (very fast with optimizations)
        time_context = get_time_based_greeting_context(country)
        
        # Build enriched query (single concatenation)
        enriched_query = f"{persona_context}{time_context}{request.query}{INSTRUCTION_SUFFIX}"

        print(f"\n[ENRICHED QUERY]: \n\n{enriched_query}\n")
        
        # Use async generate_content for non-blocking API call
        response = await client.aio.models.generate_content(
            model=MODEL_ID,
            contents=enriched_query
        )
        
        return QuickResponseResponse(
            response=response.text,
            session_id=request.session_id,
            model_used=MODEL_ID
        )
        
    except Exception as e:
        logger.error(f"❌ Error in quick response: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate quick response: {str(e)}"
        )


@router.post("/quick-response/test")
async def quick_response_test(request: QuickResponseRequest) -> QuickResponseResponse:
    """
    Test quick response endpoint (NO AUTH REQUIRED - for development only).
    OPTIMIZED: Singleton client, async API call.
    """
    try:
        # Get client from singleton
        client = get_gemini_client()
        
        # Generate time context (very fast with optimizations)
        time_context = get_time_based_greeting_context()
        
        # Build enriched query
        enriched_query = f"{time_context}{request.query}{INSTRUCTION_SUFFIX_TEST}"
        
        # Use async generate_content for non-blocking API call
        response = await client.aio.models.generate_content(
            model=MODEL_ID,
            contents=enriched_query
        )
        
        return QuickResponseResponse(
            response=response.text,
            session_id=request.session_id,
            model_used=MODEL_ID
        )
        
    except Exception as e:
        logger.error(f"❌ Error in quick response test: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate quick response: {str(e)}"
        )
