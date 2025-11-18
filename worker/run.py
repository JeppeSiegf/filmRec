import sys
from datetime import datetime, timedelta

from celery import Celery
import os
sys.path.insert(0, os.path.dirname(__file__))

from celery.schedules import crontab
from worker.services.update_log import UpdateLog
from worker.services.requests import APIService

broker_url = os.getenv("CELERY_BROKER_URL")
result_backend = os.getenv("CELERY_RESULT_BACKEND")

app = Celery("celery_app", broker=broker_url, backend=result_backend)


app.conf.update_logger = UpdateLog(os.getenv("UPDATELOG_URL"))
app.conf.api_service = APIService()
app.autodiscover_tasks(['services'])

app.conf.timezone = 'UTC'

from services.tasks import test
test.apply_async(

    eta=datetime.utcnow() + timedelta(seconds=10)  # or any time in future
)


# app.conf.beat_schedule = {
#     'scrape_data': {
#         'task': 'services.tasks.update_database',
#         'schedule': crontab(minute=0, hour=2, day_of_week=0),
#         'kwargs': {
#             'user': 'kordian86',
#             'title': 'all-the-movies-3',
#
#         }
#     },
# }



