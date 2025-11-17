FROM python:3.11-slim

WORKDIR /app

# Copy both directories from parent context
COPY worker /app/worker
COPY dataCollectors /app/dataCollectors

# Install requirements
RUN pip install --no-cache-dir -r /app/worker/requirements.txt

# Set working directory to worker
WORKDIR /app/worker

CMD ["sh", "-c", "sleep 5 && celery -A run:app worker --beat --loglevel=info"]