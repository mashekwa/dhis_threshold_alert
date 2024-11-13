try:
    from flask import Flask
    from celery import Celery
    from datetime import timedelta
except Exception as e:
    print("Error : {} ".format(e))

def make_celery(app):
    celery = Celery(app.import_name, backend=app.config['CELERY_BACKEND'],
                    broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery


app = Flask(__name__)
app.config['CELERY_BACKEND'] = "redis://redis:6379/0"
app.config['CELERY_BROKER_URL'] = "redis://redis:6379/0"
app.config['broker_connection_retry_on_startup'] = True

app.config['beat_schedule'] = {
    # 'say-every-5-seconds': {
    #     'task': 'return_something',
    #     'schedule': timedelta(seconds=10)
    # },
    'get-dhis-data-every-5-minutes': {
        'task': 'run_alerts',
        'schedule': timedelta(minutes=2)
    },
    'get-users': {
        'task': 'get_users',
        'schedule': timedelta(minutes=5)
    },

}

app.config['timezone'] = 'Africa/Harare'


celery_app = make_celery(app)

# Import tasks after celery_app is defined
from .tasks import return_something, run_alerts, get_users
