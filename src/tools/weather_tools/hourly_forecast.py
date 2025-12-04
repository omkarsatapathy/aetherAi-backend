"""Hourly weather forecast tool using Google Weather API."""
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional
from ...config import Config
from ...logging_config import get_logger
from ..google_maps import (
    get_current_session_id,
    _get_user_location_from_session,
    LocationRequiredException
)

logger = get_logger("chatbot.weather.hourly")

# Import tomorrow forecast to ensure it runs after hourly
from .daily_forecast import get_tomorrow_forecast


def get_hourly_forecast(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    hours: int = 6
) -> str:
    """
    Get hourly weather forecast for the next N hours.

    Args:
        latitude: Latitude coordinate of the location (optional, will request from user if not provided)
        longitude: Longitude coordinate of the location (optional, will request from user if not provided)
        hours: Number of hours to forecast (default: 6, max: 240)

    Returns:
        Formatted hourly weather forecast information
    """
    try:
        # Try to get location from session if not provided
        if latitude is None or longitude is None:
            session_id = get_current_session_id()
            lat, lng = _get_user_location_from_session(session_id)
        else:
            lat, lng = latitude, longitude

    except LocationRequiredException as e:
        # Return a special marker that triggers location request in frontend
        logger.info(f"Location required for hourly forecast, returning request marker")
        return "LOCATION_REQUIRED"
    except Exception as e:
        logger.error(f"Error getting location: {e}")
        return f"Failed to get location: {str(e)}"

    try:
        # Google Weather API endpoint for hourly forecast
        url = "https://weather.googleapis.com/v1/forecast/hours:lookup"

        params = {
            'key': Config.GOOGLE_SEARCH_API_KEY,
            'location.latitude': lat,
            'location.longitude': lng,
            'hours': min(hours, 240),  # Cap at maximum
            'pageSize': hours
        }

        logger.info(f"Fetching hourly forecast for ({lat}, {lng}) - next {hours} hours")

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Format the response
        if 'forecastHours' not in data or not data['forecastHours']:
            return "No hourly forecast data available for this location."

        forecast_hours = data['forecastHours'][:hours]

        result = f"**{hours}-Hour Weather Forecast**\n\n"

        for hour_data in forecast_hours:
            # Parse displayDateTime for time display
            display_dt = hour_data.get('displayDateTime', {})
            hour = display_dt.get('hours', 0)
            # Format hour in 12-hour format
            am_pm = "AM" if hour < 12 else "PM"
            display_hour = hour if hour <= 12 else hour - 12
            if display_hour == 0:
                display_hour = 12
            time_str = f"{display_hour}:00 {am_pm}"

            # Temperature - API uses 'degrees' not 'value'
            temp = hour_data.get('temperature', {})
            temp_value = temp.get('degrees', 'N/A')
            temp_unit = temp.get('unit', 'CELSIUS')
            # Simplify unit display
            unit_display = '°C' if 'CELSIUS' in temp_unit else '°F'

            # Feels like temperature
            feels_like = hour_data.get('feelsLikeTemperature', {})
            feels_like_value = feels_like.get('degrees')

            # Weather condition - API uses 'weatherCondition' with nested 'description.text'
            condition = hour_data.get('weatherCondition', {})
            condition_desc = condition.get('description', {})
            if isinstance(condition_desc, dict):
                condition_text = condition_desc.get('text', 'N/A')
            else:
                condition_text = str(condition_desc) if condition_desc else 'N/A'

            # Humidity - API uses 'relativeHumidity' as integer
            humidity = hour_data.get('relativeHumidity', 'N/A')

            # Precipitation - API uses nested structure
            precip = hour_data.get('precipitation', {})
            precip_prob = precip.get('probability', {}).get('percent', 0)

            # Wind - API uses nested structure with 'direction.cardinal' and 'speed.value'
            wind = hour_data.get('wind', {})
            wind_speed = wind.get('speed', {}).get('value', 'N/A')
            wind_unit = wind.get('speed', {}).get('unit', 'KILOMETERS_PER_HOUR')
            wind_unit_display = 'km/h' if 'KILOMETERS' in wind_unit else 'mph'
            wind_direction = wind.get('direction', {}).get('cardinal', '')

            # UV Index
            uv_index = hour_data.get('uvIndex', 'N/A')

            # Build the result string
            result += f"**{time_str}**\n"
            result += f"🌡️ Temperature: {temp_value}{unit_display}"
            if feels_like_value is not None:
                result += f" (feels like {feels_like_value}{unit_display})"
            result += f"\n☁️ Condition: {condition_text}\n"
            result += f"💧 Humidity: {humidity}%\n"
            result += f"🌧️ Precipitation: {precip_prob}%\n"

            if wind_speed != 'N/A':
                result += f"💨 Wind: {wind_speed} {wind_unit_display}"
                if wind_direction:
                    result += f" {wind_direction}"
                result += "\n"

            if uv_index != 'N/A':
                result += f"☀️ UV Index: {uv_index}\n"

            result += "\n"

        logger.info(f"Successfully fetched hourly forecast for {hours} hours")

        # MANDATORY: Always fetch tomorrow's forecast after hourly forecast
        logger.info(f"Automatically fetching tomorrow's forecast after hourly forecast")
        tomorrow_result = get_tomorrow_forecast(latitude=lat, longitude=lng)

        # Combine both results
        combined_result = result + "\n---\n\n" + tomorrow_result

        return combined_result

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error fetching hourly forecast: {e}")
        if e.response.status_code == 400:
            return "Invalid location coordinates provided."
        elif e.response.status_code == 403:
            return "Weather API access denied. Please check API key configuration."
        else:
            return f"Failed to fetch hourly forecast: {str(e)}"
    except Exception as e:
        logger.error(f"Error fetching hourly forecast: {e}")
        return f"Failed to fetch hourly forecast: {str(e)}"
