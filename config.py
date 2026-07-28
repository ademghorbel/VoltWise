"""
Configuration for the PV Production Dashboard
"""
import os
from dotenv import load_dotenv

# Force reload environment variables
load_dotenv(override=True)

# API Configuration
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")

# Weather API Settings
WEATHER_API_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
WEATHER_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

# Model Configuration
MODEL_PATH = "project_model.pkl"

# Feature columns as they appear in training data
FEATURE_COLUMNS_TIMESTAMP_ONLY = [
    'day_Friday', 'day_Monday', 'day_Saturday', 'day_Sunday', 
    'day_Thursday', 'day_Tuesday', 'day_Wednesday', 'hour'
]

FEATURE_COLUMNS_EXOGENOUS = [
    'hour', 'Vitesse vent(m/s)', 'Humidité ambiante(%RH)', 
    'Température ambiante(℃)', 'Irradiation transitoire pente(W/㎡)',
    'day_Friday', 'day_Monday', 'day_Saturday', 'day_Sunday', 
    'day_Thursday', 'day_Tuesday', 'day_Wednesday'
]

# Weather conditions mapping
WEATHER_CONDITIONS = {
    'sunny': ['Clear', 'Sunny'],
    'cloudy': ['Clouds', 'Overcast'],
    'rainy': ['Rain', 'Drizzle'],
    'stormy': ['Thunderstorm'],
    'snowy': ['Snow']
}

# Decision thresholds
IRRADIATION_THRESHOLD_HIGH = 500  # W/m²
IRRADIATION_THRESHOLD_MEDIUM = 200  # W/m²
TEMPERATURE_RANGE = (5, 45)  # Optimal temperature range in Celsius
