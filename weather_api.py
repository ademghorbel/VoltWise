"""
Weather API Integration for PV Production Dashboard
Fetches weather data and forecast from Open-Meteo (free, no API key needed)
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HOURLY_VARS = "temperature_2m,relative_humidity_2m,wind_speed_10m,cloud_cover,weather_code,precipitation"

# WMO weather codes -> (condition, description), same style as before
WMO_CODES = {
    0: ("Clear", "clear sky"), 1: ("Clear", "mainly clear"), 2: ("Clouds", "partly cloudy"),
    3: ("Clouds", "overcast"), 45: ("Fog", "fog"), 48: ("Fog", "depositing rime fog"),
    51: ("Drizzle", "light drizzle"), 53: ("Drizzle", "drizzle"), 55: ("Drizzle", "dense drizzle"),
    56: ("Drizzle", "freezing drizzle"), 57: ("Drizzle", "dense freezing drizzle"),
    61: ("Rain", "light rain"), 63: ("Rain", "rain"), 65: ("Rain", "heavy rain"),
    66: ("Rain", "freezing rain"), 67: ("Rain", "heavy freezing rain"),
    71: ("Snow", "light snow"), 73: ("Snow", "snow"), 75: ("Snow", "heavy snow"), 77: ("Snow", "snow grains"),
    80: ("Rain", "light showers"), 81: ("Rain", "showers"), 82: ("Rain", "violent showers"),
    85: ("Snow", "snow showers"), 86: ("Snow", "heavy snow showers"),
    95: ("Thunderstorm", "thunderstorm"), 96: ("Thunderstorm", "thunderstorm with hail"),
    99: ("Thunderstorm", "thunderstorm with heavy hail"),
}


def _condition(code) -> Tuple[str, str]:
    return WMO_CODES.get(int(code or 0), ("Clouds", "unknown"))


class WeatherDataFetcher:
    """Fetch and process weather data from Open-Meteo"""
    
    def __init__(self, api_key: str = ""):
        # Open-Meteo needs no key; the argument stays so older calls keep working
        self._coords = {}
    
    def _locate(self, city: str, country_code: str = "") -> Tuple[float, float]:
        """City name -> (latitude, longitude). Raises LookupError ('404') if not found."""
        key = (city.lower(), country_code.upper())
        if key in self._coords:
            return self._coords[key]
        params = {'name': city, 'count': 10, 'language': 'en', 'format': 'json'}
        if country_code:
            params['countryCode'] = country_code.upper()
        response = requests.get(GEOCODE_URL, params=params, timeout=10)
        response.raise_for_status()
        results = response.json().get('results') or []
        if not results:
            raise LookupError(f"404 Not Found: no location named '{city}'"
                              + (f" in {country_code.upper()}" if country_code else ""))
        place = results[0]
        self._coords[key] = (place['latitude'], place['longitude'])
        return self._coords[key]
    
    def _fetch(self, city: str, country_code: str, forecast_days: int) -> Dict:
        lat, lon = self._locate(city, country_code)
        params = {
            'latitude': lat, 'longitude': lon,
            'current': HOURLY_VARS, 'hourly': HOURLY_VARS,
            'wind_speed_unit': 'ms', 'timezone': 'auto', 'forecast_days': forecast_days,
        }
        response = requests.get(FORECAST_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def get_current_weather(self, city: str, country_code: str = "") -> Dict:
        """
        Fetch current weather for a location
        
        Args:
            city: City name
            country_code: ISO 3166 country code (optional)
        
        Returns:
            Dictionary with weather data
        """
        try:
            cur = self._fetch(city, country_code, 1)['current']
            condition, description = _condition(cur.get('weather_code'))
            return {
                'status': 'success',
                'data': {
                    'temperature': cur['temperature_2m'],
                    'humidity': cur['relative_humidity_2m'],
                    'wind_speed': cur['wind_speed_10m'],
                    'description': description,
                    'condition': condition,
                    'clouds': cur['cloud_cover'],
                    'timestamp': datetime.fromisoformat(cur['time'])
                }
            }
        except (requests.exceptions.RequestException, LookupError, KeyError, ValueError) as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_forecast(self, city: str, country_code: str = "", hours: int = 48) -> Dict:
        """
        Fetch weather forecast for the next hours, in 3-hour steps (as the dashboard expects)
        
        Args:
            city: City name
            country_code: ISO 3166 country code (optional)
            hours: Number of hours to forecast
        
        Returns:
            Dictionary with forecast data
        """
        try:
            data = self._fetch(city, country_code, min(16, hours // 24 + 2))
            h = data['hourly']
            now = datetime.fromisoformat(data['current']['time'])
            forecast_data = []
            for i, t in enumerate(h['time']):
                ts = datetime.fromisoformat(t)
                if ts <= now or ts.hour % 3 != 0:
                    continue
                if len(forecast_data) >= hours // 3:
                    break
                condition, description = _condition(h['weather_code'][i])
                forecast_data.append({
                    'timestamp': ts,
                    'temperature': h['temperature_2m'][i],
                    'humidity': h['relative_humidity_2m'][i],
                    'wind_speed': h['wind_speed_10m'][i],
                    'description': description,
                    'condition': condition,
                    'clouds': h['cloud_cover'][i],
                    'rain': h['precipitation'][i] or 0,
                })
            
            return {
                'status': 'success',
                'data': forecast_data
            }
        except (requests.exceptions.RequestException, LookupError, KeyError, ValueError) as e:
            return {'status': 'error', 'message': str(e)}
    
    def estimate_irradiation(self, cloud_percentage: float, hour: int) -> float:
        """
        Estimate irradiation based on cloud coverage and hour of day
        This is a simplified model - in production use a proper solar irradiation model
        
        Args:
            cloud_percentage: Cloud coverage 0-100%
            hour: Hour of day (0-23)
        
        Returns:
            Estimated irradiation in W/m²
        """
        # Base irradiation curve for clear sky (simplified)
        if hour < 6 or hour > 18:
            base_irradiation = 0
        elif 6 <= hour < 9:
            base_irradiation = (hour - 6) * 100
        elif 9 <= hour < 12:
            base_irradiation = 300 + (hour - 9) * 100
        elif 12 <= hour < 15:
            base_irradiation = 600 + (hour - 12) * 50
        elif 15 <= hour < 18:
            base_irradiation = 750 - (hour - 15) * 100
        else:
            base_irradiation = 0
        
        # Apply cloud reduction factor
        cloud_reduction = 1 - (cloud_percentage / 100) * 0.9
        estimated = base_irradiation * max(cloud_reduction, 0)
        
        return max(estimated, 0)
    
    def format_for_model(self, weather_data: Dict) -> Dict:
        """
        Format weather data to match model input columns
        
        Args:
            weather_data: Weather data dictionary from API
        
        Returns:
            Dictionary with columns matching the ML model
        """
        timestamp = weather_data['timestamp']
        
        # Calculate hour of day
        hour = timestamp.hour
        
        # One-hot encode day of week
        day_name = timestamp.strftime('%A')
        day_columns = {
            'day_Friday': 1 if day_name == 'Friday' else 0,
            'day_Monday': 1 if day_name == 'Monday' else 0,
            'day_Saturday': 1 if day_name == 'Saturday' else 0,
            'day_Sunday': 1 if day_name == 'Sunday' else 0,
            'day_Thursday': 1 if day_name == 'Thursday' else 0,
            'day_Tuesday': 1 if day_name == 'Tuesday' else 0,
            'day_Wednesday': 1 if day_name == 'Wednesday' else 0,
        }
        
        # Estimate irradiation
        irradiation = self.estimate_irradiation(
            weather_data['clouds'],
            hour
        )
        
        formatted_data = {
            'hour': hour,
            'Vitesse vent(m/s)': weather_data['wind_speed'],
            'Humidité ambiante(%RH)': weather_data['humidity'],
            'Température ambiante(℃)': weather_data['temperature'],
            'Irradiation transitoire pente(W/㎡)': irradiation,
            **day_columns,
            'timestamp': timestamp,
            'weather_condition': weather_data['condition'],
            'cloud_coverage': weather_data['clouds']
        }
        
        return formatted_data

def get_weather_data(city: str, country_code: str = "") -> Tuple[Dict, Dict]:
    """
    Convenience function to fetch current weather and forecast
    
    Args:
        city: City name
        country_code: ISO 3166 country code (optional)
    
    Returns:
        Tuple of (current_weather, forecast)
    """
    fetcher = WeatherDataFetcher()
    current = fetcher.get_current_weather(city, country_code)
    forecast = fetcher.get_forecast(city, country_code)
    return current, forecast
