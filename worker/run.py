from datetime import datetime, timedelta

from celery import Celery
import os

from celery.schedules import crontab
from services.update_log import UpdateLog
from services.requests import APIService

broker_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

app = Celery("celery_app", broker=broker_url, backend=result_backend)

app.conf.update_logger = UpdateLog(host="redis", port=6379, db=1)
app.conf.api_service = APIService()
app.autodiscover_tasks(['services'])

app.conf.timezone = 'UTC'

from services.tasks import update_database
#update_database.apply_async(
#     kwargs={'user': 'kordian86', 'title': 'all-the-movies-3'},
#     eta=datetime.utcnow() + timedelta(seconds=10)  # or any time in future
# )


app.conf.beat_schedule = {
    'scrape_data': {
        'task': 'services.tasks.update_database',
        'schedule': crontab(minute=0, hour=2, day_of_week=0),
        'kwargs': {
            'user': 'kordian86',
            'title': 'all-the-movies-3',

        }
    },
}



