"""Daily weather forecast tools using Google Weather API."""
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

logger = get_logger("chatbot.weather.daily")


def get_tomorrow_forecast(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> str:
    """
    Get tomorrow's weather forecast.

    Args:
        latitude: Latitude coordinate of the location (optional, will request from user if not provided)
        longitude: Longitude coordinate of the location (optional, will request from user if not provided)

    Returns:
        Formatted tomorrow's weather forecast information
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
        logger.info(f"Location required for tomorrow's forecast, returning request marker")
        return "LOCATION_REQUIRED"
    except Exception as e:
        logger.error(f"Error getting location: {e}")
        return f"Failed to get location: {str(e)}"

    try:
        # Google Weather API endpoint for daily forecast
        url = "https://weather.googleapis.com/v1/forecast/days:lookup"

        params = {
            'key': Config.GOOGLE_SEARCH_API_KEY,
            'location.latitude': lat,
            'location.longitude': lng,
            'days': 2,  # Get today and tomorrow
            'pageSize': 2
        }

        logger.info(f"Fetching tomorrow's forecast for ({lat}, {lng})")

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Format the response
        if 'forecastDays' not in data or len(data['forecastDays']) < 2:
            return "Tomorrow's forecast data is not available for this location."

        # Get tomorrow's forecast (index 1)
        tomorrow = data['forecastDays'][1]

        result = "**Tomorrow's Weather Forecast**\n\n"

        # Parse displayDate for date display
        display_date = tomorrow.get('displayDate', {})
        date_str = f"{display_date.get('year', '')}-{display_date.get('month', ''):02d}-{display_date.get('day', ''):02d}" if display_date else 'Unknown date'
        result += f"📅 Date: {date_str}\n\n"

        # Temperature - API uses 'maxTemperature' and 'minTemperature' with 'degrees'
        max_temp = tomorrow.get('maxTemperature', {})
        min_temp = tomorrow.get('minTemperature', {})
        temp_unit = max_temp.get('unit', 'CELSIUS')
        unit_display = '°C' if 'CELSIUS' in temp_unit else '°F'

        result += f"🌡️ **Temperature:**\n"
        result += f"   High: {max_temp.get('degrees', 'N/A')}{unit_display}\n"
        result += f"   Low: {min_temp.get('degrees', 'N/A')}{unit_display}\n\n"

        # Daytime forecast (7 AM - 7 PM) - API uses 'daytimeForecast'
        daytime = tomorrow.get('daytimeForecast', {})
        if daytime:
            condition = daytime.get('weatherCondition', {})
            condition_desc = condition.get('description', {})
            condition_text = condition_desc.get('text', 'N/A') if isinstance(condition_desc, dict) else str(condition_desc)

            # Precipitation - nested structure
            precip = daytime.get('precipitation', {})
            precip_prob = precip.get('probability', {}).get('percent', 0)

            result += f"**Daytime (7 AM - 7 PM):**\n"
            result += f"☁️ Condition: {condition_text}\n"
            result += f"🌧️ Precipitation: {precip_prob}%\n"

            wind = daytime.get('wind', {})
            if wind:
                wind_speed = wind.get('speed', {}).get('value', 'N/A')
                wind_unit = wind.get('speed', {}).get('unit', 'KILOMETERS_PER_HOUR')
                wind_unit_display = 'km/h' if 'KILOMETERS' in wind_unit else 'mph'
                result += f"💨 Wind: {wind_speed} {wind_unit_display}\n"

            result += f"💧 Humidity: {daytime.get('relativeHumidity', 'N/A')}%\n"
            result += f"☀️ UV Index: {daytime.get('uvIndex', 'N/A')}\n\n"

        # Nighttime forecast (7 PM - 7 AM) - API uses 'nighttimeForecast'
        nighttime = tomorrow.get('nighttimeForecast', {})
        if nighttime:
            condition = nighttime.get('weatherCondition', {})
            condition_desc = condition.get('description', {})
            condition_text = condition_desc.get('text', 'N/A') if isinstance(condition_desc, dict) else str(condition_desc)

            # Precipitation - nested structure
            precip = nighttime.get('precipitation', {})
            precip_prob = precip.get('probability', {}).get('percent', 0)

            result += f"**Nighttime (7 PM - 7 AM):**\n"
            result += f"☁️ Condition: {condition_text}\n"
            result += f"🌧️ Precipitation: {precip_prob}%\n"

            wind = nighttime.get('wind', {})
            if wind:
                wind_speed = wind.get('speed', {}).get('value', 'N/A')
                wind_unit = wind.get('speed', {}).get('unit', 'KILOMETERS_PER_HOUR')
                wind_unit_display = 'km/h' if 'KILOMETERS' in wind_unit else 'mph'
                result += f"💨 Wind: {wind_speed} {wind_unit_display}\n"

            result += f"💧 Humidity: {nighttime.get('relativeHumidity', 'N/A')}%\n\n"

        # Sunrise/Sunset - API uses 'sunEvents' with 'sunriseTime' and 'sunsetTime'
        sun_events = tomorrow.get('sunEvents', {})
        if sun_events:
            result += f"**Sun Times:**\n"
            sunrise = sun_events.get('sunriseTime', '')
            sunset = sun_events.get('sunsetTime', '')

            # Get timezone from API response for local time conversion
            timezone_id = data.get('timeZone', {}).get('id', 'Asia/Kolkata')
            try:
                local_tz = ZoneInfo(timezone_id)
            except:
                local_tz = ZoneInfo('Asia/Kolkata')  # Fallback to IST

            if sunrise:
                # Parse ISO 8601 time and convert to local timezone
                try:
                    sunrise_dt = datetime.fromisoformat(sunrise.replace('Z', '+00:00'))
                    sunrise_local = sunrise_dt.astimezone(local_tz)
                    result += f"🌅 Sunrise: {sunrise_local.strftime('%I:%M %p')}\n"
                except Exception as e:
                    logger.error(f"Error parsing sunrise: {e}")
                    result += f"🌅 Sunrise: {sunrise}\n"
            if sunset:
                try:
                    sunset_dt = datetime.fromisoformat(sunset.replace('Z', '+00:00'))
                    sunset_local = sunset_dt.astimezone(local_tz)
                    result += f"🌇 Sunset: {sunset_local.strftime('%I:%M %p')}\n"
                except Exception as e:
                    logger.error(f"Error parsing sunset: {e}")
                    result += f"🌇 Sunset: {sunset}\n"

        logger.info(f"Successfully fetched tomorrow's forecast")
        return result

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error fetching tomorrow's forecast: {e}")
        if e.response.status_code == 400:
            return "Invalid location coordinates provided."
        elif e.response.status_code == 403:
            return "Weather API access denied. Please check API key configuration."
        else:
            return f"Failed to fetch tomorrow's forecast: {str(e)}"
    except Exception as e:
        logger.error(f"Error fetching tomorrow's forecast: {e}")
        return f"Failed to fetch tomorrow's forecast: {str(e)}"


def get_five_day_forecast(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> str:
    """
    Get 5-day weather forecast.

    Args:
        latitude: Latitude coordinate of the location (optional, will request from user if not provided)
        longitude: Longitude coordinate of the location (optional, will request from user if not provided)

    Returns:
        Formatted 5-day weather forecast information
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
        logger.info(f"Location required for 5-day forecast, returning request marker")
        return "LOCATION_REQUIRED"
    except Exception as e:
        logger.error(f"Error getting location: {e}")
        return f"Failed to get location: {str(e)}"

    try:
        # Google Weather API endpoint for daily forecast
        url = "https://weather.googleapis.com/v1/forecast/days:lookup"

        params = {
            'key': Config.GOOGLE_SEARCH_API_KEY,
            'location.latitude': lat,
            'location.longitude': lng,
            'days': 5,
            'pageSize': 5
        }

        logger.info(f"Fetching 5-day forecast for ({lat}, {lng})")

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Format the response
        if 'forecastDays' not in data or not data['forecastDays']:
            return "5-day forecast data is not available for this location."

        forecast_days = data['forecastDays'][:5]

        result = "**5-Day Weather Forecast**\n\n"

        for day_data in forecast_days:
            # Parse displayDate for date display
            display_date = day_data.get('displayDate', {})
            date_str = f"{display_date.get('year', '')}-{display_date.get('month', ''):02d}-{display_date.get('day', ''):02d}" if display_date else 'Unknown date'

            # Temperature - API uses 'maxTemperature' and 'minTemperature' with 'degrees'
            max_temp = day_data.get('maxTemperature', {})
            min_temp = day_data.get('minTemperature', {})
            temp_unit = max_temp.get('unit', 'CELSIUS')
            unit_display = '°C' if 'CELSIUS' in temp_unit else '°F'

            result += f"📅 **{date_str}**\n"
            result += f"🌡️ High: {max_temp.get('degrees', 'N/A')}{unit_display} | "
            result += f"Low: {min_temp.get('degrees', 'N/A')}{unit_display}\n"

            # Daytime summary - API uses 'daytimeForecast'
            daytime = day_data.get('daytimeForecast', {})
            if daytime:
                condition = daytime.get('weatherCondition', {})
                condition_desc = condition.get('description', {})
                condition_text = condition_desc.get('text', 'N/A') if isinstance(condition_desc, dict) else str(condition_desc)

                # Precipitation - nested structure
                precip = daytime.get('precipitation', {})
                precip_prob = precip.get('probability', {}).get('percent', 0)

                result += f"☁️ {condition_text}\n"
                result += f"🌧️ Precipitation: {precip_prob}%"

                thunderstorm_prob = day_data.get('thunderstormProbability', 0)
                if thunderstorm_prob and thunderstorm_prob > 0:
                    result += f" | ⛈️ Thunderstorm: {thunderstorm_prob}%"

                result += "\n"

            result += "\n"

        logger.info(f"Successfully fetched 5-day forecast")
        return result

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error fetching 5-day forecast: {e}")
        if e.response.status_code == 400:
            return "Invalid location coordinates provided."
        elif e.response.status_code == 403:
            return "Weather API access denied. Please check API key configuration."
        else:
            return f"Failed to fetch 5-day forecast: {str(e)}"
    except Exception as e:
        logger.error(f"Error fetching 5-day forecast: {e}")
        return f"Failed to fetch 5-day forecast: {str(e)}"
