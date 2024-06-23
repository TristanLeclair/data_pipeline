#!/bin/bash

trap "exit" INT TERM
trap "kill 0" EXIT

docker-compose exec kafka kafka-console-consumer.sh --topic weather --from-beginning --bootstrap-server kafka:9092
