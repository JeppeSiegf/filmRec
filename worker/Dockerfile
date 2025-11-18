FROM python:3.11-slim

WORKDIR /app/worker

COPY worker/ /app/worker/
COPY dataCollectors/ /app/dataCollectors/

COPY worker/requirements.txt /app/worker/requirements.txt
RUN pip install --no-cache-dir -r /app/worker/requirements.txt

ENV PYTHONPATH=/app

CMD ["celery", "-A", "run:app", "worker", "--beat", "--loglevel=info"]