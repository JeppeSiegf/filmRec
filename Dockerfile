# Use official Python slim image
FROM python:3.10-slim

# Install system dependencies (keep build tools until after pip install)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    g++ \
    wget \
    && wget -O /wait-for-it.sh https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh \
    && chmod +x /wait-for-it.sh \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies WHILE build tools are still available
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# Remove build dependencies after pip install
RUN apt-get purge -y --auto-remove build-essential gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Create entrypoint script
RUN printf '#!/bin/sh\n\
echo "Waiting for Docker DNS to resolve db..."\n\
until getent hosts db; do\n\
  echo "Still waiting on DNS for db..."\n\
  sleep 1\n\
done\n\
echo "DNS resolved for db, now waiting for Postgres..."\n\
/wait-for-it.sh db:5432 --timeout=60\n\
echo "Database ready! Starting app..."\n\
exec gunicorn --bind 0.0.0.0:5000 run:app\n' > /entrypoint.sh \
    && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]