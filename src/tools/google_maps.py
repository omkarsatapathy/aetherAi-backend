"""Google Maps grounding tool using Gemini API for location-aware responses."""
import json
import os
import requests
from typing import Optional, Dict, Any, List
from contextvars import ContextVar
from google import genai
from google.genai import types
from ..config import Config
from ..logging_config import get_logger

logger = get_logger("chatbot.tools.google_maps")

# Context variable to store current session ID for tools
_current_session_id: ContextVar[Optional[str]] = ContextVar('current_session_id', default=None)


class LocationRequiredException(Exception):
    """Raised when user location is required but not available in session."""
    pass

# Lazy-load Gemini client to avoid initialization errors when env vars are missing
_client = None

def _get_client():
    """Get or initialize the Gemini client."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=Config.GEMINI_API_KEY)
    return _client

# Default coordinates (Hyderabad, India) - used only as fallback
DEFAULT_LATITUDE = 17.473863
DEFAULT_LONGITUDE = 78.351742

# Global session state storage for location data
_session_location_store = {}


def set_current_session_id(session_id: str):
    """Set the current session ID in context for tools to access."""
    _current_session_id.set(session_id)


def get_current_session_id() -> Optional[str]:
    """Get the current session ID from context."""
    return _current_session_id.get()


def _get_user_location_from_session(session_id: Optional[str] = None) -> tuple[float, float]:
    """
    Get user location from session state.

    Args:
        session_id: Optional session ID to retrieve location for

    Returns:
        Tuple of (latitude, longitude)

    Raises:
        LocationRequiredException: If location not found in session
    """
    if session_id and session_id in _session_location_store:
        loc = _session_location_store[session_id]
        logger.info(f"Retrieved user location from session: ({loc['latitude']}, {loc['longitude']})")
        return loc['latitude'], loc['longitude']

    # Location not available - raise exception to trigger frontend request
    logger.warning(f"User location not found in session {session_id}, requesting from user")
    raise LocationRequiredException("User location required for maps functionality")


def set_user_location(session_id: str, latitude: float, longitude: float):
    """
    Store user location in session.

    Args:
        session_id: Session identifier
        latitude: User's latitude
        longitude: User's longitude
    """
    _session_location_store[session_id] = {
        'latitude': latitude,
        'longitude': longitude
    }
    logger.info(f"Stored user location for session {session_id}: ({latitude}, {longitude})")


def clear_user_location(session_id: str):
    """
    Clear user location from session.

    Args:
        session_id: Session identifier
    """
    if session_id in _session_location_store:
        del _session_location_store[session_id]
        logger.info(f"Cleared user location for session {session_id}")


# Google Maps API Key for Places API (use same key as Gemini or dedicated Maps key)
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "") or Config.GEMINI_API_KEY


def _fetch_place_details(place_id: str, place_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetch place details including reviews from Google Places API.

    Args:
        place_id: The Google Place ID
        place_name: Name of the place for logging context

    Returns:
        Dictionary with place details or None if fetch fails
    """
    if not GOOGLE_MAPS_API_KEY:
        logger.warning("GOOGLE_MAPS_API_KEY not set, skipping place details fetch")
        return None

    clean_place_id = place_id.replace("places/", "") if place_id.startswith("places/") else place_id

    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": clean_place_id,
        "fields": "name,rating,user_ratings_total,reviews,formatted_address,types,price_level",
        "key": GOOGLE_MAPS_API_KEY
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "OK":
            logger.warning(f"Places API error for {place_name}: {data.get('status')}")
            return None

        result = data.get("result", {})

        place_details = {
            "place_id": place_id,
            "name": result.get("name", place_name),
            "rating": result.get("rating"),
            "total_ratings": result.get("user_ratings_total", 0),
            "address": result.get("formatted_address", ""),
            "types": result.get("types", []),
            "price_level": result.get("price_level"),
            "reviews": []
        }

        for review in result.get("reviews", []):
            place_details["reviews"].append({
                "author": review.get("author_name", "Anonymous"),
                "rating": review.get("rating", 0),
                "time": review.get("relative_time_description", ""),
                "text": review.get("text", "")
            })

        logger.info(f"Fetched details for {place_name}: rating={place_details['rating']}, reviews={len(place_details['reviews'])}")
        return place_details

    except Exception as e:
        logger.error(f"Failed to fetch details for {place_name}: {e}")
        return None


def _rank_places_with_llm(places_data: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    """
    Use LLM to analyze and rank places based on reviews and ratings.
    Returns top 3 places with reasons and highlighted features.

    Args:
        places_data: List of place details with reviews
        query: Original search query for context

    Returns:
        List of top 3 ranked places with analysis
    """
    if not places_data:
        return []

    # Build context for LLM
    places_context = []
    for i, place in enumerate(places_data, 1):
        reviews_text = "\n".join([
            f"  - {r['author']} ({r['rating']}/5): {r['text'][:300]}"
            for r in place.get("reviews", [])[:5]
        ])

        places_context.append(f"""
Place {i}: {place['name']}
- Place ID: {place['place_id']}
- Rating: {place.get('rating', 'N/A')}/5 ({place.get('total_ratings', 0)} reviews)
- Address: {place.get('address', 'N/A')}
- Type: {', '.join(place.get('types', [])[:3])}
- Price Level: {'$' * place.get('price_level', 0) if place.get('price_level') else 'N/A'}
- Recent Reviews:
{reviews_text if reviews_text else '  No reviews available'}
""")

    prompt = f"""Analyze these places based on the user's search: "{query}"

{chr(10).join(places_context)}

Based on the ratings, reviews, and relevance to the search query, select the TOP 3 BEST places.

For each selected place, provide:
1. Why it's ranked at this position (based on reviews and ratings)
2. Best features, signature items, or standout services mentioned in reviews
3. What makes it special compared to others

Return ONLY valid JSON in this exact format:
{{
  "ranked_places": [
    {{
      "rank": 1,
      "place_id": "the exact place_id from above",
      "name": "place name",
      "rating": 4.5,
      "reason": "2-3 sentences explaining why this is the top choice based on reviews",
      "highlights": ["signature dish/service 1", "feature 2", "what reviewers loved"],
      "best_for": "brief description of ideal customer (e.g., 'Perfect for family dinners' or 'Best for quick business lunches')"
    }},
    {{
      "rank": 2,
      ...
    }},
    {{
      "rank": 3,
      ...
    }}
  ]
}}

Focus on extracting specific items, dishes, services, or features that reviewers praised. Be specific - mention actual menu items, service qualities, or unique offerings."""

    try:
        client = _get_client()
        response = client.models.generate_content(
            model=Config.GEMINI_MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
            )
        )

        response_text = response.text.strip()

        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        ranked_data = json.loads(response_text)
        ranked_places = ranked_data.get("ranked_places", [])

        logger.info(f"LLM ranked {len(ranked_places)} places from {len(places_data)} candidates")
        return ranked_places

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM ranking response: {e}")
        # Fallback: return places sorted by rating
        return _fallback_ranking(places_data)
    except Exception as e:
        logger.error(f"LLM ranking failed: {e}")
        return _fallback_ranking(places_data)


def _fallback_ranking(places_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Fallback ranking when LLM fails - sort by rating."""
    sorted_places = sorted(
        places_data,
        key=lambda x: (x.get("rating") or 0, x.get("total_ratings") or 0),
        reverse=True
    )[:3]

    return [
        {
            "rank": i + 1,
            "place_id": p["place_id"],
            "name": p["name"],
            "rating": p.get("rating"),
            "reason": f"Ranked #{i+1} based on overall rating of {p.get('rating', 'N/A')}/5",
            "highlights": [],
            "best_for": ""
        }
        for i, p in enumerate(sorted_places)
    ]


def query_maps_with_gemini(
    query: str,
    latitude: float = DEFAULT_LATITUDE,
    longitude: float = DEFAULT_LONGITUDE,
    include_widget: bool = True,
    radius_km: Optional[float] = None
) -> Dict[str, Any]:
    """
    Query Google Maps using Gemini's Maps grounding feature.
    Fetches places, analyzes reviews with LLM, and returns ranked recommendations.

    Args:
        query: The location-related query
        latitude: Latitude coordinate for location context
        longitude: Longitude coordinate for location context
        include_widget: Whether to include widget token for map rendering
        radius_km: Optional search radius in kilometers (e.g., 1.0 for 1km, 5.0 for 5km)

    Returns:
        Dictionary with response text, widget token, ranked places, and grounding metadata
    """
    try:
        enhanced_query = query
        if radius_km is not None:
            enhanced_query = f"{query} within {radius_km}km radius"
            logger.info(f"Maps query with radius: '{enhanced_query}' at ({latitude}, {longitude})")
        else:
            logger.info(f"Maps query: '{query}' at ({latitude}, {longitude})")

        client = _get_client()

        response = client.models.generate_content(
            model=Config.GEMINI_MODEL_ID,
            contents=enhanced_query,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_maps=types.GoogleMaps(enable_widget=include_widget))],
                tool_config=types.ToolConfig(
                    retrieval_config=types.RetrievalConfig(
                        lat_lng=types.LatLng(
                            latitude=latitude,
                            longitude=longitude
                        )
                    )
                )
            )
        )

        result = {
            "text": response.text,
            "widget_token": None,
            "places": [],
            "ranked_places": [],
            "coordinates": {"latitude": latitude, "longitude": longitude}
        }

        # Extract grounding metadata for widget rendering
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                metadata = candidate.grounding_metadata

                if hasattr(metadata, 'google_maps_widget_context_token') and metadata.google_maps_widget_context_token:
                    result["widget_token"] = metadata.google_maps_widget_context_token
                    logger.info("Maps widget token extracted")

                if hasattr(metadata, 'grounding_chunks') and metadata.grounding_chunks:
                    for chunk in metadata.grounding_chunks:
                        if hasattr(chunk, 'maps') and chunk.maps:
                            place_data = {
                                "place_id": getattr(chunk.maps, 'place_id', ''),
                                "title": getattr(chunk.maps, 'title', ''),
                                "uri": getattr(chunk.maps, 'uri', '')
                            }
                            result["places"].append(place_data)
                            logger.info(f"Found place: {place_data['title']} (place_id: {place_data['place_id']})")

        # Fetch detailed reviews for all places and rank them
        if result["places"]:
            places_with_details = []
            for place in result["places"]:
                if place["place_id"]:
                    details = _fetch_place_details(place["place_id"], place["title"])
                    if details:
                        details["uri"] = place.get("uri", "")
                        places_with_details.append(details)

            # Rank places using LLM if we have enough data
            if places_with_details:
                logger.info(f"Ranking {len(places_with_details)} places with LLM analysis")
                result["ranked_places"] = _rank_places_with_llm(places_with_details, query)

                # Merge URI info into ranked places
                place_uri_map = {p["place_id"]: p.get("uri", "") for p in places_with_details}
                for ranked in result["ranked_places"]:
                    ranked["uri"] = place_uri_map.get(ranked.get("place_id"), "")

        logger.info(f"Maps response: {len(result['text'])} chars, places: {len(result['places'])}, ranked: {len(result['ranked_places'])}")
        return result

    except Exception as e:
        logger.error(f"Google Maps query failed: {e}")
        raise


def format_maps_response(result: Dict[str, Any]) -> str:
    """
    Format maps response with ranked places and widget metadata for frontend rendering.

    Args:
        result: Dictionary from query_maps_with_gemini

    Returns:
        Formatted string with text and embedded metadata including ranked recommendations
    """
    response_text = result["text"]

    has_maps_data = result.get("widget_token") or len(result.get("places", [])) > 0
    has_ranked_places = len(result.get("ranked_places", [])) > 0

    if has_maps_data or has_ranked_places:
        metadata = {
            "maps_widget": {
                "context_token": result.get("widget_token"),
                "coordinates": result["coordinates"],
                "places": result.get("places", [])[:10],
                "ranked_recommendations": result.get("ranked_places", [])
            }
        }
        response_text += f"\n\n<!--MAPS_WIDGET:{json.dumps(metadata)}-->"
        logger.info(f"Added maps metadata: {len(metadata['maps_widget']['places'])} places, {len(metadata['maps_widget']['ranked_recommendations'])} ranked")

    return response_text


# @tool
def search_nearby_places(
    query: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: Optional[float] = None
) -> str:
    """
    Search for nearby places, restaurants, businesses, or points of interest.

    Use this tool when the user asks about:
    - Nearby restaurants, cafes, shops, or businesses
    - Places to visit or attractions in an area
    - Finding specific types of establishments (hospitals, ATMs, gas stations, etc.)

    Args:
        query: What to search for (e.g., "best Italian restaurants", "nearby hospitals")
        latitude: Optional latitude coordinate (will request from user if not provided)
        longitude: Optional longitude coordinate (will request from user if not provided)
        radius_km: Optional search radius in kilometers (e.g., 1.0 for 1km, 5.0 for 5km).
                   If not specified, uses default nearby search (~2-5km depending on query)

    Returns:
        Information about nearby places matching the query with optional maps widget

    Examples:
        - "coffee shops" with radius_km=1.0 → searches within 1km
        - "restaurants" with radius_km=5.0 → searches within 5km
        - "gas stations" with no radius → uses default nearby search
    """
    try:
        # Try to get location from session if not provided
        if latitude is None or longitude is None:
            session_id = get_current_session_id()
            lat, lng = _get_user_location_from_session(session_id)
        else:
            lat, lng = latitude, longitude

        result = query_maps_with_gemini(query, lat, lng, radius_km=radius_km)
        return format_maps_response(result)

    except LocationRequiredException as e:
        # Return a special marker that triggers location request in frontend
        logger.info(f"Location required for tool, returning request marker")
        return "LOCATION_REQUIRED"
    except Exception as e:
        logger.error(f"search_nearby_places error: {e}")
        return f"Failed to search nearby places: {str(e)}"


# @tool
def get_directions(
    origin: str,
    destination: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> str:
    """
    Get directions and travel information between two locations.

    Use this tool when the user asks about:
    - How to get from one place to another
    - Travel routes and directions
    - Distance and estimated travel time between locations

    Args:
        origin: Starting location or address
        destination: Destination location or address
        latitude: Optional latitude for context (will request from user if not provided)
        longitude: Optional longitude for context (will request from user if not provided)

    Returns:
        Directions and travel information with optional maps widget
    """
    try:
        # Try to get location from session if not provided
        if latitude is None or longitude is None:
            session_id = get_current_session_id()
            lat, lng = _get_user_location_from_session(session_id)
        else:
            lat, lng = latitude, longitude

        query = f"How do I get from {origin} to {destination}? Provide directions and estimated travel time."
        result = query_maps_with_gemini(query, lat, lng)
        return format_maps_response(result)

    except LocationRequiredException as e:
        # Return a special marker that triggers location request in frontend
        logger.info(f"Location required for tool, returning request marker")
        return "LOCATION_REQUIRED"
    except Exception as e:
        logger.error(f"get_directions error: {e}")
        return f"Failed to get directions: {str(e)}"


# @tool
def get_traffic_info(
    location: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> str:
    """
    Get current traffic conditions and updates for an area.

    Use this tool when the user asks about:
    - Current traffic conditions
    - Road congestion or traffic jams
    - Best time to travel or commute

    Args:
        location: Optional specific location or route to check traffic for
        latitude: Optional latitude coordinate (will request from user if not provided)
        longitude: Optional longitude coordinate (will request from user if not provided)

    Returns:
        Current traffic information and conditions with optional maps widget
    """
    try:
        # Try to get location from session if not provided
        if latitude is None or longitude is None:
            session_id = get_current_session_id()
            lat, lng = _get_user_location_from_session(session_id)
        else:
            lat, lng = latitude, longitude

        if location:
            query = f"What is the current traffic situation near {location}? Include any congestion, road conditions, or delays."
        else:
            query = "What is the current traffic situation in this area? Include any congestion, major road conditions, or delays."

        result = query_maps_with_gemini(query, lat, lng)
        return format_maps_response(result)

    except LocationRequiredException as e:
        # Return a special marker that triggers location request in frontend
        logger.info(f"Location required for tool, returning request marker")
        return "LOCATION_REQUIRED"
    except Exception as e:
        logger.error(f"get_traffic_info error: {e}")
        return f"Failed to get traffic info: {str(e)}"


# @tool
def get_place_details(
    place_name: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> str:
    """
    Get detailed information about a specific place or business.

    Use this tool when the user asks about:
    - Operating hours of a business
    - Reviews and ratings of a place
    - Contact information or address
    - Details about a specific restaurant, shop, or attraction

    Args:
        place_name: Name of the place to get details about
        latitude: Optional latitude for context (will request from user if not provided)
        longitude: Optional longitude for context (will request from user if not provided)

    Returns:
        Detailed information about the place with optional maps widget
    """
    try:
        # Try to get location from session if not provided
        if latitude is None or longitude is None:
            session_id = get_current_session_id()
            lat, lng = _get_user_location_from_session(session_id)
        else:
            lat, lng = latitude, longitude

        query = f"Tell me about {place_name}. Include its address, operating hours, ratings, reviews, and any other relevant details."
        result = query_maps_with_gemini(query, lat, lng)
        return format_maps_response(result)

    except LocationRequiredException as e:
        # Return a special marker that triggers location request in frontend
        logger.info(f"Location required for tool, returning request marker")
        return "LOCATION_REQUIRED"
    except Exception as e:
        logger.error(f"get_place_details error: {e}")
        return f"Failed to get place details: {str(e)}"


# @tool
def explore_area(
    area: Optional[str] = None,
    interests: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: Optional[float] = None
) -> str:
    """
    Explore and discover interesting places in an area based on interests.

    Use this tool when the user wants to:
    - Discover what's around them
    - Find things to do in an area
    - Get recommendations based on interests
    - Plan activities or outings

    Args:
        area: Optional specific area or neighborhood to explore
        interests: Optional interests or preferences (e.g., "family-friendly", "nightlife", "outdoor activities")
        latitude: Optional latitude coordinate (will request from user if not provided)
        longitude: Optional longitude coordinate (will request from user if not provided)
        radius_km: Optional search radius in kilometers for exploration

    Returns:
        Recommendations and interesting places to explore with optional maps widget
    """
    try:
        # Try to get location from session if not provided
        if latitude is None or longitude is None:
            session_id = get_current_session_id()
            lat, lng = _get_user_location_from_session(session_id)
        else:
            lat, lng = latitude, longitude

        if area and interests:
            query = f"What are some interesting places to visit in {area} for someone interested in {interests}? Include popular attractions, hidden gems, and recommendations."
        elif area:
            query = f"What are the best places to visit and things to do in {area}? Include popular attractions, restaurants, and local favorites."
        elif interests:
            query = f"What are some nearby places for someone interested in {interests}? Include recommendations and suggestions."
        else:
            query = "What are some interesting places to visit and things to do nearby? Include popular attractions, restaurants, and local favorites."

        result = query_maps_with_gemini(query, lat, lng, radius_km=radius_km)
        return format_maps_response(result)

    except LocationRequiredException as e:
        # Return a special marker that triggers location request in frontend
        logger.info(f"Location required for tool, returning request marker")
        return "LOCATION_REQUIRED"
    except Exception as e:
        logger.error(f"explore_area error: {e}")
        return f"Failed to explore area: {str(e)}"


def get_location_name(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> str:
    """
    Get the name of a location (city/area) from coordinates using reverse geocoding.

    Use this tool to get the user's location name for personalized responses.
    For example, to greet users with "Good morning from Hyderabad!"

    Args:
        latitude: Optional latitude coordinate (will use session location if not provided)
        longitude: Optional longitude coordinate (will use session location if not provided)

    Returns:
        Location name string (e.g., "Hyderabad", "Mumbai, Maharashtra")
    """
    try:
        # Try to get location from session if not provided
        if latitude is None or longitude is None:
            session_id = get_current_session_id()
            lat, lng = _get_user_location_from_session(session_id)
        else:
            lat, lng = latitude, longitude

        logger.info(f"Getting location name for ({lat}, {lng})")

        # Use Gemini to get location name via Maps grounding
        client = _get_client()

        response = client.models.generate_content(
            model=Config.GEMINI_MODEL_ID,
            contents=f"What is the name of the city or area at coordinates {lat}, {lng}? Reply with just the location name, like 'Hyderabad' or 'Banjara Hills, Hyderabad'. Keep it short.",
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_maps=types.GoogleMaps())],
                tool_config=types.ToolConfig(
                    retrieval_config=types.RetrievalConfig(
                        lat_lng=types.LatLng(
                            latitude=lat,
                            longitude=lng
                        )
                    )
                )
            )
        )

        location_name = response.text.strip()
        logger.info(f"Location name resolved: {location_name}")
        return location_name

    except LocationRequiredException as e:
        logger.info(f"Location required for reverse geocoding, returning request marker")
        return "LOCATION_REQUIRED"
    except Exception as e:
        logger.error(f"get_location_name error: {e}")
        return "your area"  # Fallback gracefully


def get_place_reviews(place_id: str) -> Dict[str, Any]:
    """
    Fetch detailed place information including reviews from Google Places API.

    Args:
        place_id: The Google Place ID (e.g., "ChIJN1t_tDeuEmsRUsoyG83frY4")

    Returns:
        Dictionary containing place details and reviews
    """
    if not GOOGLE_MAPS_API_KEY:
        logger.error("GOOGLE_MAPS_API_KEY not set in environment")
        return {"error": "Google Maps API key not configured"}

    # Remove "places/" prefix if present (Gemini returns "places/ChIJ..." but API expects "ChIJ...")
    clean_place_id = place_id.replace("places/", "") if place_id.startswith("places/") else place_id

    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": clean_place_id,
        "fields": "name,rating,user_ratings_total,reviews,formatted_address,opening_hours,website,price_level,types",
        "key": GOOGLE_MAPS_API_KEY
    }

    try:
        logger.info(f"Fetching place details for place_id: {place_id}")
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "OK":
            logger.error(f"Places API error: {data.get('status')} - {data.get('error_message', '')}")
            return {"error": f"Places API error: {data.get('status')}"}

        result = data.get("result", {})

        # Format the response
        place_info = {
            "name": result.get("name"),
            "rating": result.get("rating"),
            "total_ratings": result.get("user_ratings_total"),
            "address": result.get("formatted_address"),
            "website": result.get("website"),
            "price_level": result.get("price_level"),
            "types": result.get("types", []),
            "opening_hours": None,
            "reviews": []
        }

        # Extract opening hours
        if result.get("opening_hours"):
            place_info["opening_hours"] = {
                "open_now": result["opening_hours"].get("open_now"),
                "weekday_text": result["opening_hours"].get("weekday_text", [])
            }

        # Extract reviews
        for review in result.get("reviews", []):
            place_info["reviews"].append({
                "author": review.get("author_name"),
                "rating": review.get("rating"),
                "time": review.get("relative_time_description"),
                "text": review.get("text")
            })

        logger.info(f"Successfully fetched details for '{place_info['name']}' with {len(place_info['reviews'])} reviews")
        return place_info

    except requests.RequestException as e:
        logger.error(f"Request failed for place_id {place_id}: {e}")
        return {"error": f"Failed to fetch place details: {str(e)}"}


def print_place_reviews(place_id: str) -> None:
    """
    Fetch and print place reviews in a readable format.

    Args:
        place_id: The Google Place ID
    """
    result = get_place_reviews(place_id)

    if "error" in result:
        print(f"Error: {result['error']}")
        return

    print("=" * 60)
    print(f"Name: {result['name']}")
    print(f"Rating: {result['rating']}/5 ({result['total_ratings']} reviews)")
    print(f"Address: {result['address']}")
    if result['website']:
        print(f"Website: {result['website']}")
    if result['price_level']:
        print(f"Price Level: {'$' * result['price_level']}")

    if result['opening_hours']:
        print(f"\nCurrently Open: {'Yes' if result['opening_hours']['open_now'] else 'No'}")
        if result['opening_hours']['weekday_text']:
            print("Hours:")
            for hours in result['opening_hours']['weekday_text']:
                print(f"  {hours}")

    print("\n" + "=" * 60)
    print("REVIEWS:")
    print("=" * 60)

    for i, review in enumerate(result['reviews'], 1):
        print(f"\n--- Review {i} ---")
        print(f"Author: {review['author']}")
        print(f"Rating: {'⭐' * review['rating']}")
        print(f"Time: {review['time']}")
        print(f"Review: {review['text']}")

    print("\n" + "=" * 60)


def search_and_get_reviews(
    query: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Search for places and fetch reviews for each result.

    This combines the Gemini Maps search with the Places API to get
    both place discovery and detailed reviews.

    Args:
        query: Search query (e.g., "best restaurants nearby")
        latitude: Optional latitude coordinate
        longitude: Optional longitude coordinate

    Returns:
        List of place details with reviews
    """
    try:
        # First, search for places using Gemini
        if latitude is None or longitude is None:
            session_id = get_current_session_id()
            lat, lng = _get_user_location_from_session(session_id)
        else:
            lat, lng = latitude, longitude

        result = query_maps_with_gemini(query, lat, lng)
        places_with_reviews = []

        # For each place found, fetch detailed reviews
        for place in result.get("places", []):
            place_id = place.get("place_id")
            if place_id:
                logger.info(f"Fetching reviews for: {place.get('title')}")
                reviews_data = get_place_reviews(place_id)
                if "error" not in reviews_data:
                    places_with_reviews.append(reviews_data)

        logger.info(f"Found {len(places_with_reviews)} places with reviews")
        return places_with_reviews

    except LocationRequiredException:
        logger.info("Location required for search_and_get_reviews")
        return [{"error": "LOCATION_REQUIRED"}]
    except Exception as e:
        logger.error(f"search_and_get_reviews error: {e}")
        return [{"error": str(e)}]


# Quick test function
if __name__ == "__main__":
    # Test with a sample place ID (Sydney Opera House)
    test_place_id = "ChIJN1t_tDeuEmsRUsoyG83frY4"
    print_place_reviews(test_place_id)
