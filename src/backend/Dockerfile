# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Configure Poetry: Don't create virtual environment, install dependencies globally
RUN poetry config virtualenvs.create false

# Copy Poetry files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry install --only=main --no-root --no-interaction --no-ansi

# Copy application code
COPY app/ ./app/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Run the application
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
