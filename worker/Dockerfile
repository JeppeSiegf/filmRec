FROM python:3.11-slim

# Workdir inside container
WORKDIR /app

COPY worker/ /app/worker/


COPY dataCollectors/ /app/dataCollectors/


COPY worker/requirements.txt /app/worker/requirements.txt
RUN pip install --no-cache-dir -r /app/worker/requirements.txt

# Set Python path so imports work relative to current workdir
ENV PYTHONPATH=.

# Start Celery
CMD ["celery", "-A", "worker.run:app", "worker", "--beat", "--loglevel=info"]
