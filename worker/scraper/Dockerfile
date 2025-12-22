FROM python:3.11-slim

WORKDIR /app/worker/scraper/

COPY worker/scraper/ /app/worker/scraper/
COPY dataCollectors/ /app/dataCollectors/
COPY worker/services/ /app/worker/services/

RUN pip install --no-cache-dir -r /app/worker/scraper/requirements.txt

ENV PYTHONPATH=/app

CMD ["celery", "-A", "worker.scraper.run:app", "call", "tasks.test"]