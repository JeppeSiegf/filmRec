FROM python:3.11-slim
FROM python:3.11-slim

WORKDIR /app/worker

# copy requirements first (cache friendly)
COPY worker/requirements.txt /app/worker/requirements.txt
RUN pip install --no-cache-dir -r /app/worker/requirements.txt

# copy contents (note trailing slash /)
COPY worker/ /app/worker
COPY dataCollectors /app/dataCollectors

# Set PYTHONPATH so imports work from worker directory
ENV PYTHONPATH=/app/worker:/app

CMD ["celery", "-A", "run:app", "worker", "--beat", "--loglevel=info"]