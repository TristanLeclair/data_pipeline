# Python and Kafka Weather Data Streaming

## Overview

This project is a comprehensive data processing pipeline utilizing Kafka for input and data transformation. The pipeline includes data production, consumption, and various transformation services using QuixStreams. It is built with Python, Docker, and supporting scripts to manage data flow and transformations.

### Data

The data comes from [open-meteo API](https://open-meteo.com/). I got a large historical dataset instead of streaming from their API (though the functionality is implemented), to save on unnecessary API calls. My producer script streams the csv data line by line to emulate real-time gathering.

### Producers

The producer service gathers data from [open-meteo API](https://open-meteo.com/) to feed into Kafka.

> **_NOTE:_** I've left in the normal streaming code that calls the [open-meteo API](https://open-meteo.com/) but have replaced the default "fetcher" with a json reader that simulates receiving real-time data by pulling from a csv file to save on API calls.

### Transformers

Services that perform specific data transformations.

#### Transformer Average

transformer_average.py: Script to calculate average temperature every minute.

#### Transformer High Low Open Close

transformer_high_low_open_close.py: Script to calculate high, low, open, and close values of temperature, humidity and wind speeds every 5 minutes.

#### Transformer i18n

transformer_i18n.py: Script for internationalization of temperature data.

### Docker compose

All my services are built and run through docker compose. Zookeeper and kafka images first spin up, followed by the producer and transformers.

#### Networking

All services are run on a custom-set docker bridge network.

> **_NOTE:_** Kafka is available on the network through port 9092, though with the bitnami image it is accessible through the hostname "kafka" instead. See [bitnami documentation](https://hub.docker.com/r/bitnami/kafka) "Using a Docker Compose file"
> It is also available locally on port 9093 (for use with kcat or other tooling). See [bitnami documentation](https://hub.docker.com/r/bitnami/kafka) "Accessing Apache Kafka with internal and external clients".

### Technologies

- Python
  - QuixStreams
- Kafka
- Docker
- docker-compose
