FROM python:3.11-slim

WORKDIR /app/worker

COPY worker /app/worker
COPY dataCollectors /app/dataCollectors

RUN pip install --no-cache-dir -r requirements.txt

CMD ["celery", "-A", "run:app", "worker", "--beat", "--loglevel=info"]