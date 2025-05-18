# Use official Python slim image
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update \
    && apt-get install -y \
        build-essential \
        libpq-dev \
        gcc \
        g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# Copy application code
COPY . .

# Start the application directly
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
