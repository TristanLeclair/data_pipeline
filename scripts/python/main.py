import json
import logging
import time
from typing import Literal
from pathlib import Path

import openmeteo_requests
from tap import Tap
import requests
import requests_cache
from retry_requests import retry

# region Setup


class Parser(Tap):
    locations: (
        Path  # JSON file that contains latitude and longitude of area we want to query
    )
    log_level: Literal[
        "CRITICAL", "FATAL", "ERROR", "WARN", "WARNING", "INFO", "DEBUG", "NOTSET"
    ] = "WARNING"  # Log level
    loop: bool = False  # Loop application and keep fetching and sending to kafka


def setup():
    cache_session = requests_cache.CachedSession(".cache", expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    return openmeteo


# endregion
# region Get from API


def read_location_info(locations_file_path) -> tuple[float, float]:
    try:
        with open(locations_file_path) as f:
            locations = json.load(f)
            try:
                lat = float(locations["latitude"])
                lon = float(locations["longitude"])
            except ValueError:
                logging.error("Invalid JSON coordinates, must be floats")
                exit(1)
    except FileNotFoundError:
        logging.error(f"Invalid file path: {locations_file_path}")
        exit(1)

    return lat, lon


request_sender_types = Literal["openmeteo", "requests"]


def create_params(lat: float, lon: float):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ["temperature_2m", "wind_speed_10m"],
        "forecast_days": 1,
    }

    return url, params


def send_request(lat: float, lon: float):
    url, params = create_params(lat, lon)

    response = requests.get(url, params=params)

    return response.json()


def send_request_open_meteo(lat: float, lon: float):
    url, params = create_params(lat, lon)
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    return response


# endregion
# region Stream data
# endregion


def main(options: Parser):
    global openmeteo
    openmeteo = setup()

    lat, lon = read_location_info(options.locations)
    logging.info(f"Pulling weather information from lat:{lat}, lon:{lon}")

    response = send_request(lat, lon)
    print(json.dumps(response.json()))


if __name__ == "__main__":
    options = Parser().parse_args()
    print(options)
    logging.basicConfig(level=options.log_level.upper())
    main(options)
