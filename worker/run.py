from app import app as app
from celery.schedules import crontab

app.conf.beat_schedule = {
    'scrape_data': {
        'task': 'update',
        'schedule': crontab(minute=0, hour=2, day_of_week=0),
        'kwargs': {
            'user': 'kordian86',
            'title': 'all-the-movies-3',
        }},
    'scrape_data_weekly': {
        'task': 'update',
        'schedule': crontab(minute=0, hour=3, day_of_week=1),
        'kwargs': {
            'user': 'hershwin',
            'title': 'all-the-movies',
        }},
}

if __name__ == '__main__':
    app.worker_main(['worker', '-B', '-l', 'debug'])