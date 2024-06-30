import logging

from quixstreams import Application
from quixstreams.kafka.consumer import AutoOffsetReset
from quixstreams.logging import LogLevel
from tap import Tap

# region Parser


class Parser(Tap):
    log_level: LogLevel = "DEBUG"  # Log level
    kafka_broker_address: str = "localhost:9093"  # address of kafka server
    kafka_consumer_group: str = "weather_transformer"
    # """Consumer group for Kafka, will generate a random uuid everytime if left empty"""
    kafka_input_topic: str = "weather_input_topic"  # Kafka topic to subscribe to
    kafka_output_topic: str = "weather_i18n"
    kafka_offset_reset: AutoOffsetReset = "earliest"  # Kafka offset reset option


# endregion


def main():
    app = Application(
        broker_address=options.kafka_broker_address,
        loglevel=options.log_level,
        consumer_group=(options.kafka_consumer_group),
        auto_offset_reset=options.kafka_offset_reset,
    )

    input_topic = app.topic(options.kafka_input_topic)
    output_topic = app.topic(options.kafka_output_topic)

    def transform(msg):
        current = msg["current"]
        celcius = float(current["temperature_2m"])
        fahrenheit = (celcius * 9 / 5) + 32
        kelvin = celcius + 273.15
        new_msg = {
            "celcius": celcius,
            "fahrenheit": round(fahrenheit, 2),
            "kelvin": round(kelvin, 2),
        }

        logging.debug(f"Returning: {new_msg}")
        return new_msg

    sdf = app.dataframe(input_topic)
    sdf = sdf.apply(transform)
    sdf = sdf.to_topic(output_topic)

    app.run(sdf)


if __name__ == "__main__":
    global options
    options = Parser().parse_args()
    logging.basicConfig(level=options.log_level)
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Stopping by KeyboardInterrupt")
        pass
