.PHONY: dev run install sync clean

# Start development server with hot reload
dev:
	uv run uvicorn app.main:app --reload

# Start production server
run:
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# Install dependencies
install:
	uv sync

# Sync dependencies (update lockfile)
sync:
	uv lock
	uv sync

# Clean cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
