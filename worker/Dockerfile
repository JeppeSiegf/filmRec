FROM python:3.11-slim

# Workdir inside container
WORKDIR /app/worker

# Copy worker/ into /app/worker
COPY worker/ /app/worker

# Copy dataCollectors/ from repo root into /app/dataCollectors
# NOTE: path is from the *build context*, not relative to this Dockerfile.
COPY dataCollectors/ /app/dataCollectors

# Install requirements (worker has its own requirements)
COPY worker/requirements.txt /app/worker/requirements.txt
RUN pip install --no-cache-dir -r /app/worker/requirements.txt

ENV PYTHONPATH=/app/worker:/app

CMD ["celery", "-A", "run:app", "worker", "--beat", "--loglevel=info"]
