.PHONY: start-consumer start-producer

# Start consumer through docker-compose exec
start-consumer:
	@./scripts/bash/start_consumer.sh

# Start producer through docker-compose exec
start-producer:
	@./scripts/bash/start_producer.sh

# Run fetch once, can pipe to jq for prettier output
run-fetch-once:
	@python3 scripts/python/main.py --locations locations.json
