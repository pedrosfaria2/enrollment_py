# Enrollment System

FastAPI-based enrollment management system with RabbitMQ message processing.

## Documentation

Complete API documentation available in the `documentation/` folder. Open `documentation/index.html` in a browser.

When running the application, interactive API documentation is available at:
- `/docs` - Swagger UI
- `/redoc` - ReDoc

## Dependencies

- Python 3.12+
- uv (Python package manager)
- Docker & Docker Compose
- make
- ruff (linting and formatting)

## Setup

```bash
make setup
```

This installs dependencies and sets up the project in editable mode.

An `.env_example` file is provided for configuration reference. For testing, copy it to `.env` in the root directory.

## Running

### Local Development
```bash
# API server
make run

# Worker/consumer
make run-worker
```

### Docker Compose (Recommended)
```bash
# Run all services (API + Worker + RabbitMQ)
make run-compose

# Run with logs visible
make run-compose-logs

# View logs from running services
make compose-logs

# Stop services
make stop-compose
```

## Testing

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src --cov-report=term --cov-report=html

# Using Makefile
make test
make test-coverage
```

## Code Quality

```bash
# Lint code
uv run ruff check .

# Lint and fix issues
uv run ruff check . --fix

# Format code
uv run ruff format .

# Using Makefile
make lint
make lint-fix
make format
make check  # runs both lint and format
```

## Makefile Commands

- `make setup` - Install dependencies
- `make run` - Run API server
- `make run-worker` - Run worker/consumer
- `make run-compose` - Run full stack with Docker Compose
- `make run-compose-logs` - Run with visible logs
- `make compose-logs` - Show logs from running containers
- `make stop-compose` - Stop Docker services
- `make test` - Run tests
- `make test-coverage` - Run tests with coverage
- `make lint` - Check code quality
- `make lint-fix` - Fix linting issues
- `make format` - Format code
- `make check` - Run lint and format checks
