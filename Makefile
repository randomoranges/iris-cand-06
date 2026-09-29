# Convenience wrapper around the documented commands. `make help` lists targets.
.PHONY: help up down init run test clean

help:
	@echo "up     - start PostGIS (docker compose up -d)"
	@echo "init   - apply schema + load fixtures (qa init-db)"
	@echo "run    - run QA over all datasets (qa run --all)"
	@echo "test   - run the acceptance-criteria tests (pytest)"
	@echo "down   - stop PostGIS"
	@echo "clean  - stop PostGIS and delete its data volume"

up:
	docker compose up -d

init:
	qa init-db

run:
	qa run --all

test:
	pytest -q

down:
	docker compose down

clean:
	docker compose down -v
