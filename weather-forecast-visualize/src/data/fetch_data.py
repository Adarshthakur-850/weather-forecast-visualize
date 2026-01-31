import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw"
DATA_FILE = RAW_DATA_PATH / "weather_data.csv"

RAW_DATA_PATH.mkdir(parents=True, exist_ok=True)

def fetch_weather_data():
    """Fetches historical weather data from Open-Meteo API."""
    
    cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    params = {
        "latitude": 51.5074,
        "longitude": -0.1278,
        "start_date": "2023-01-01",
        "end_date": "2024-01-30",
        "hourly": ["temperature_2m", "relative_humidity_2m", "rain", "surface_pressure"],
        "timezone": "auto"
    }

    logging.info(f"Fetching weather data for coordinates: {params['latitude']}, {params['longitude']}...")
    url = "https://archive-api.open-meteo.com/v1/archive"
    responses = openmeteo.weather_api(url, params=params)

    response = responses[0]
    
    logging.info(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    logging.info(f"Elevation {response.Elevation()} m asl")

    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
    hourly_rain = hourly.Variables(2).ValuesAsNumpy()
    hourly_surface_pressure = hourly.Variables(3).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
        end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = hourly.Interval()),
        inclusive = "left"
    )}
    
    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m
    hourly_data["rain"] = hourly_rain
    hourly_data["surface_pressure"] = hourly_surface_pressure

    df = pd.DataFrame(data = hourly_data)
    
    logging.info(f"Fetched {len(df)} rows of data.")
    
    df.to_csv(DATA_FILE, index=False)
    logging.info(f"Data saved to {DATA_FILE}")

if __name__ == "__main__":
    fetch_weather_data()
