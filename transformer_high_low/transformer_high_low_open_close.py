from datetime import timedelta
import logging
from typing import Tuple
from uuid import uuid4

from quixstreams import Application
from quixstreams.kafka.consumer import AutoOffsetReset
from quixstreams.logging import LogLevel
from tap import Tap

# region Parser


class Parser(Tap):
    log_level: LogLevel = "DEBUG"  # Log level
    kafka_broker_address: str = "localhost:9093"  # address of kafka server
    # kafka_consumer_group: str = "weather_high_low_open_close"
    kafka_consumer_group: str = str(uuid4())
    # """Consumer group for Kafka, will generate a random uuid everytime if left empty"""
    kafka_input_topic: str = "weather_input_topic"  # Kafka topic to subscribe to
    kafka_output_topic: str = "weather_high_low_open_close"
    kafka_offset_reset: AutoOffsetReset = "earliest"  # Kafka offset reset option


# endregion


def extract_values(msg) -> Tuple[float, float, float]:
    temperature = float(msg["current"]["temperature_2m"])
    wind_speed = float(msg["current"]["wind_speed_10m"])
    humidity = float(msg["current"]["relative_humidity_2m"])
    return temperature, wind_speed, humidity


def reducer_func(agg, msg):
    temperature, wind_speed, humidity = extract_values(msg)
    return {
        "temperature": {
            "open": agg["temperature"]["open"],
            "close": temperature,
            "high": max(agg["temperature"]["high"], temperature),
            "low": min(agg["temperature"]["low"], temperature),
        },
        "wind_speed": {
            "open": agg["wind_speed"]["open"],
            "close": wind_speed,
            "high": max(agg["wind_speed"]["high"], wind_speed),
            "low": min(agg["wind_speed"]["low"], wind_speed),
        },
        "humidity": {
            "open": agg["humidity"]["open"],
            "close": humidity,
            "high": max(agg["humidity"]["high"], humidity),
            "low": min(agg["humidity"]["low"], humidity),
        },
    }


def initializer_func(msg):
    temperature, wind_speed, humidity = extract_values(msg)
    return {
        "temperature": {
            "open": temperature,
            "close": temperature,
            "high": temperature,
            "low": temperature,
        },
        "wind_speed": {
            "open": wind_speed,
            "close": wind_speed,
            "high": wind_speed,
            "low": wind_speed,
        },
        "humidity": {
            "open": humidity,
            "close": humidity,
            "high": humidity,
            "low": humidity,
        },
    }


def main():
    app = Application(
        broker_address=options.kafka_broker_address,
        loglevel=options.log_level,
        consumer_group=options.kafka_consumer_group,
        auto_offset_reset=options.kafka_offset_reset,
    )

    input_topic = app.topic(options.kafka_input_topic)
    output_topic = app.topic(options.kafka_output_topic)

    sdf = app.dataframe(input_topic)

    # Uses Kafka's timestamp, not timestamp in data
    sdf = sdf.tumbling_window(duration_ms=timedelta(minutes=5))

    # Reduce to create high low open close every 5 minutes
    sdf = sdf.reduce(reducer=reducer_func, initializer=initializer_func)
    sdf = sdf.final()
    sdf = sdf.update(lambda msg: logging.debug(f"Got {msg}"))
    sdf = sdf.to_topic(output_topic)

    app.run(sdf)

    pass


if __name__ == "__main__":
    global options
    options = Parser().parse_args()
    logging.basicConfig(level=options.log_level)
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Stopping by KeyboardInterrupt")
