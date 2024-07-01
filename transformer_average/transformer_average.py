from datetime import timedelta
import logging
from uuid import uuid4

from quixstreams import Application
from quixstreams.kafka.consumer import AutoOffsetReset
from quixstreams.logging import LogLevel
from tap import Tap

# region Parser


class Parser(Tap):
    log_level: LogLevel = "DEBUG"  # Log level
    kafka_broker_address: str = "localhost:9093"  # address of kafka server
    kafka_consumer_group: str = "weather_average"
    # """Consumer group for Kafka, will generate a random uuid everytime if left empty"""
    kafka_input_topic: str = "weather_input_topic"  # Kafka topic to subscribe to
    kafka_output_topic: str = "weather_average"
    kafka_offset_reset: AutoOffsetReset = "earliest"  # Kafka offset reset option
    dev: bool = False  # Will override to dev defaults (random consumer group, DEBUG)

    def process_args(self) -> None:
        if self.dev:
            self.kafka_consumer_group = str(uuid4())
            self.log_level = "DEBUG"


# endregion


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
    sdf = (
        sdf.apply(lambda msg: float(msg["current"]["temperature_2m"]))
        .tumbling_window(duration_ms=timedelta(minutes=1))
        .mean()
        .final()
    )

    # Reduce to create high low open close every 5 minutes
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
