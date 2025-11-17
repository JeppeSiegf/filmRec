FROM python:3.11-slim

WORKDIR /app/worker

# copy requirements first
COPY worker/requirements.txt /app/worker/requirements.txt
RUN pip install --no-cache-dir -r /app/worker/requirements.txt

# now copy the contents of worker into /app/worker
COPY worker/ /app/worker
COPY dataCollectors /app/dataCollectors

CMD ["celery", "-A", "run:app", "worker", "--beat", "--loglevel=info"]
