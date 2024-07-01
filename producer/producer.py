import datetime
import json
import logging
import time
import random
import re
from typing import Literal, Optional
from pathlib import Path

import openmeteo_requests
from quixstreams import Application
from quixstreams.logging import LogLevel
from tap import Tap
import requests
import requests_cache
from retry_requests import retry

# region Setup


class Parser(Tap):
    """
    Python script that streams weather api information from open-meteo.com into Kafka
    """

    locations: Path  # JSON file that contains latitude and longitude of area
    log_level: LogLevel = "DEBUG"  # Log level
    loop: bool = False  # Loop application and keep fetching and sending to kafka
    data_source: Literal["csv", "requests", "openmeteo"] = "csv"  # Source of data
    csv_path: Optional[Path] = None  # csv path if data_source = "csv"
    kafka_topic: str = "weather_input_topic"  # kafka topic to stream to
    kafka_key: str = "St-Jean"  # key to give kafka data
    kafka_broker_address: str = "localhost:9093"  # kafka broker address

    def process_args(self) -> None:
        if self.data_source != "csv" and self.csv_path is not None:
            raise ValueError("csv_path is only needed when the data_source is 'csv'")
        if self.data_source == "csv" and self.csv_path is None:
            raise ValueError("csv_path is only needed when the data_source is 'csv'")


def setup():
    cache_session = requests_cache.CachedSession(".cache", expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    return openmeteo


# endregion
# region Get from API


def read_location_info(locations_file_path: Path) -> tuple[float, float]:
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
        "current": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m"],
        "forecast_days": 1,
    }

    return url, params


def send_request():
    url, params = create_params(latitude, longitude)

    response = requests.get(url, params=params)

    return response.json()


def send_request_open_meteo():
    url, params = create_params(latitude, longitude)
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    # TODO: transform data (I'm not going to use this right now,
    # would rather work with raw data for the time being)
    return json.loads('{"latitude": 45, "longitude": -73}')


class LineReader:
    def __init__(self) -> None:
        self.line_generator = self.read_lines_from_csv()

    def __call__(self):
        try:
            return next(self.line_generator)
        except StopIteration:
            return None

    def is_valid_line(self, line: str):
        pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2},-?\d+\.\d+,\d+,-?\d+\.\d+$"
        return bool(re.match(pattern, line))

    def read_lines_from_csv(self):
        assert options.data_source == "csv" and options.csv_path is not None

        with open(options.csv_path, "r") as file:
            for line in file:
                line = line.strip()
                if self.is_valid_line(line):
                    yield self.clean_line(line)

    def clean_line(self, line: str) -> dict:
        """
        Reformat csv line into a normal API response. See data/sample_data.json

        Changes time to current time instead to match with Kafka's timestamp, which will be used later
        """
        _, temp, humidity, wind_speed = line.split(",")
        json_payload = {
            "latitude": latitude,
            "longitude": longitude,
            "generationtime_ms": random.uniform(0.03, 0.09),
            "utc_offset_seconds": 0,
            "timezone": "GMT",
            "timezone_abbreviation": "GMT",
            "elevation": 30.0,
            "current_units": {
                "time": "iso8601",
                "interval": "seconds",
                "temperature_2m": "\u00b0C",
                "relative_humidity_2m": "%",
                "wind_speed_10m": "km/h",
            },
            "current": {
                "time": str(datetime.datetime.now()),
                "interval": 900,
                "temperature_2m": float(temp),
                "relative_humidity_2m": float(humidity),
                "wind_speed_10m": float(wind_speed),
            },
        }

        return json_payload


def select_correct_requester_and_delay():
    match options.data_source:
        case "csv":
            request_data = LineReader()
            delay = 0.5
        case "requests":
            request_data = send_request
            delay = 60
        case "openmeteo_requests":
            request_data = send_request_open_meteo
            delay = 60
        case _:
            request_data = LineReader()
            delay = 0.5
    return request_data, delay


# endregion
# region Stream data
# endregion


def main():
    global openmeteo
    openmeteo = setup()

    global latitude, longitude
    latitude, longitude = read_location_info(options.locations)
    logging.info(f"Pulling weather information from lat:{latitude}, lon:{longitude}")

    app = Application(
        broker_address=options.kafka_broker_address,
        loglevel=options.log_level,
    )

    # input_topic = app.topic("weather_input_topic")
    # output_topic = app.topic("weather_output_topic")

    request_data, delay_between_reads = select_correct_requester_and_delay()
    weather = request_data()

    with app.get_producer() as producer:
        while True and weather is not None:
            logging.debug(f"Got weather {json.dumps(weather)}")
            producer.produce(
                topic=options.kafka_topic,
                key=options.kafka_key,
                value=json.dumps(weather),
            )
            logging.info("Produced. Sleeping...")
            if not options.loop:
                break
            time.sleep(delay_between_reads)
            weather = request_data()


if __name__ == "__main__":
    try:
        global options
        options = Parser().parse_args()
        print(options)
        logging.basicConfig(level=options.log_level.upper())
        main()
    except KeyboardInterrupt:
        logging.info("Stopping by KeyboardInterrupt")
        pass
