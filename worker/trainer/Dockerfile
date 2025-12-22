FROM python:3.11-slim



WORKDIR /app/
RUN apt-get update && apt-get install -y \
    libgomp1 \
    build-essential \
    gcc \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

COPY worker/trainer/ /app/worker/trainer/
COPY recommendationEngine/ /app/recommendationEngine/

RUN apt-get update && apt-get install -y \
    libgomp1 \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r /app/worker/trainer/requirements.txt


ENV PYTHONPATH=/app

CMD ["python", "-u", "/app/worker/trainer/run.py"]