from celery import Celery
from .config import BROKER_URL, RESULT_BACKEND

app = Celery(
    'workers',
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=['workers.tasks']
)

app.conf.timezone = 'UTC +3'