SHELL := /bin/bash
SERVICE_NAME := $(shell git remote get-url origin | sed 's/.*\/\([^\/]*\)\.git/\1/')

.PHONY: help
help:
	@echo "Usage: make [target]"
	@echo "Targets:"
	@echo " setup          Install dependencies using uv"
	@echo " run            Run the API application"
	@echo " run-worker     Run the worker/consumer"
	@echo " run-compose    Run the full stack with Docker Compose"
	@echo " run-compose-logs Run the full stack and show logs"
	@echo " stop-compose   Stop Docker Compose services"
	@echo " compose-logs   Show logs from Docker Compose services"
	@echo " sync           Sync dependencies using uv"
	@echo " lock           Generate uv.lock file"
	@echo " test           Run tests"
	@echo " test-coverage  Run tests with coverage"
	@echo " lint           Lint the code using ruff"
	@echo " lint-fix       Lint and fix issues automatically using ruff"
	@echo " format         Format the code using ruff"
	@echo " check          Run both linting and formatting checks"

.PHONY: setup
setup:
	uv sync
	uv pip install -e .
	@echo "Dependencies installed. To activate the virtual environment, run: source .venv/bin/activate"

.PHONY: sync
sync:
	uv sync

.PHONY: lock
lock:
	uv lock

.PHONY: run
run:
	uv run src/main.py

.PHONY: run-worker
run-worker:
	uv run src/worker/consumer.py

.PHONY: run-compose
run-compose:
	docker compose -f infra/docker-compose.yml --env-file .env up -d

.PHONY: run-compose-logs
run-compose-logs:
	docker compose -f infra/docker-compose.yml --env-file .env up

.PHONY: stop-compose
stop-compose:
	docker compose -f infra/docker-compose.yml down

.PHONY: compose-logs
compose-logs:
	docker compose -f infra/docker-compose.yml logs -f

.PHONY: test
test:
	uv run pytest

.PHONY: test-coverage
test-coverage:
	uv run pytest --cov=src --cov-report=term --cov-report=html tests/

.PHONY: lint
lint:
	uv run ruff check .

.PHONY: lint-fix
lint-fix:
	uv run ruff check . --fix

.PHONY: format
format:
	uv run ruff format .

.PHONY: check
check: lint format
	@echo "All checks passed!"
