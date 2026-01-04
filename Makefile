.PHONY: dev run install install-dev sync clean test docker-build docker-run docker-up

# Start development server with hot reload
dev:
	uv run uvicorn app.main:app --reload

# Start production server
run:
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# Install dependencies
install:
	uv sync

# Install with dev dependencies
install-dev:
	uv sync --extra dev

# Sync dependencies (update lockfile)
sync:
	uv lock
	uv sync

# Run tests
test:
	uv run --extra dev pytest tests/ -v

# Build Docker image
docker-build:
	docker build -t autonomous-task-agent .

# Run Docker container
docker-run:
	docker run --rm -p 8000:8000 --env-file .env autonomous-task-agent

# Run with docker-compose
docker-up:
	docker-compose up --build

# Clean cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
