# Use official Python Alpine image
FROM python:3.10-alpine

# Install build dependencies, PostgreSQL client libraries, and C build tools
RUN apk add --no-cache \
    postgresql-dev \
    gcc \
    g++ \
    musl-dev

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose the port Gunicorn will run on
EXPOSE 5000

# Default command (can be overridden by docker-compose)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]

