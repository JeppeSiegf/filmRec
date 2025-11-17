FROM python:3.11-slim

WORKDIR /app/worker

# copy requirements first (cache friendly)
COPY worker/requirements.txt /app/worker/requirements.txt
RUN pip install --no-cache-dir -r /app/worker/requirements.txt

# copy contents (note trailing slash /)
COPY worker/ /app/worker
COPY dataCollectors /app/dataCollectors

# Make sure Python can find top-level modules in /app/worker
ENV PYTHONPATH=/app/worker

CMD ["celery", "-A", "run:app", "worker", "--beat", "--loglevel=info"]
