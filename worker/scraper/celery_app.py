import sys
from datetime import datetime, timedelta

import logging
logger = logging.getLogger(__name__)
from celery import Celery
import os
from celery.schedules import crontab


broker_url = os.getenv("CELERY_BROKER_URL")
result_backend = os.getenv("CELERY_RESULT_BACKEND")

app = Celery("celery_app", broker=broker_url, backend=result_backend)

app.conf.timezone = 'UTC'
app.conf.task_default_queue = 'scraper'

app.conf.beat_schedule = {
    'scrape_data': {
        'task': 'update',
        'schedule': crontab(minute=0, hour=2, day_of_week=0),
        'kwargs': {
            'user': 'kordian86',
            'title': 'all-the-movies-3',
        }},
    # 'test': {
    #     'task': 'test',
    #     'schedule': 10.0,
    # }
    }

app.autodiscover_tasks(['worker.scraper.tasks'])