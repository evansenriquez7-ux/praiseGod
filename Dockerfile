FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install build dependencies (sometimes needed for psycopg2 or python-magic)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code and essential data
COPY backend ./backend
COPY data ./data

# Environment variables
ENV PORT=8080
ENV PYTHONPATH=/app

# Run uvicorn server, referencing the PORT env variable that Cloud Run provides
CMD uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
