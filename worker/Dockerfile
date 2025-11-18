FROM python:3.11-slim

# Workdir inside container
WORKDIR /app

# Copy *contents* of worker/ into /app/worker
COPY worker/. /app/worker/

# Copy dataCollectors/ from repo root into /app/dataCollectors
# Make it accessible from worker via relative import
COPY dataCollectors/ /app/dataCollectors/

# Install requirements
COPY worker/requirements.txt /app/worker/requirements.txt
RUN pip install --no-cache-dir -r /app/worker/requirements.txt

# Set Python path so imports work relative to current workdir
ENV PYTHONPATH=.

# Start Celery
CMD ["celery", "-A", "run:app", "worker", "--beat", "--loglevel=info"]
