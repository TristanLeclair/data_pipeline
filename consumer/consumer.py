import logging
import json

from quixstreams import Application
from quixstreams.kafka.consumer import AutoOffsetReset
from quixstreams.logging import LogLevel
from tap import Tap

# region Parser


class Parser(Tap):
    log_level: LogLevel = "DEBUG"  # Log level
    kafka_broker_address: str = "localhost:9093"  # address of kafka server
    kafka_consumer_group: str = "weather_reader"
    """Consumer group for Kafka, will generate a random uuid everytime if left empty"""
    kafka_input_topic: str = "weather_input_topic"  # Kafka topic to subscribe to
    kafka_offset_reset: AutoOffsetReset = "earliest"  # Kafka offset reset option


# endregion


def main():
    app = Application(
        broker_address=options.kafka_broker_address,
        loglevel=options.log_level,
        consumer_group=(options.kafka_consumer_group),
        auto_offset_reset=options.kafka_offset_reset,
    )

    with app.get_consumer() as consumer:
        consumer.subscribe([options.kafka_input_topic])

        while True:
            msg = consumer.poll(1)

            if msg is None:
                print("Waiting...")
            elif msg.error() is not None:
                raise Exception(msg.error())
            else:
                key = msg.key().decode("utf8")
                value = json.loads(msg.value())
                offset = msg.offset()

                print(f"{offset} {key} {value}")


if __name__ == "__main__":
    global options
    options = Parser().parse_args()
    logging.basicConfig(level=options.log_level)
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Stopping by KeyboardInterrupt")
        pass
