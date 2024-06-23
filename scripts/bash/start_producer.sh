#!/bin/bash

trap "exit" INT TERM
trap "kill 0" EXIT

docker-compose exec kafka kafka-console-producer.sh --topic weather --broker-list kafka:9092
