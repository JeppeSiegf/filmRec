FROM python:3.11-slim

WORKDIR /app

# Copy both directories from parent context
COPY worker /app/worker
COPY dataCollectors /app/dataCollectors

# Install requirements
RUN pip install --no-cache-dir -r /app/worker/requirements.txt

CMD ["sh", "-c", "sleep 5 && celery -A worker.run:app worker --beat --loglevel=info"]