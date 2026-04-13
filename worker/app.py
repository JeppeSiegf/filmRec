import logging
logger = logging.getLogger(__name__)
from celery import Celery
import os

broker_url = os.getenv("CELERY_BROKER_URL")
result_backend = os.getenv("CELERY_RESULT_BACKEND")

app = Celery("celery_app", broker=broker_url, backend=result_backend)

app.conf.timezone = 'UTC'
app.conf.task_default_queue = 'scraper'

app.autodiscover_tasks(['tasks'])
