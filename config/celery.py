# config/celery.py
# Celery configuration

import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('claude_crm')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    'escalate-expired-approvals-every-5-minutes': {
        'task': 'workflow.escalate_expired_approvals',
        'schedule': crontab(minute='*/5'),  # Run every 5 minutes
        'options': {
            'expires': 300,  # Task expires after 5 minutes
        }
    },
    # Optional: cleanup old approvals weekly
    'cleanup-old-approvals-weekly': {
        'task': 'workflow.cleanup_old_approvals',
        'schedule': crontab(hour=0, minute=0, day_of_week=0),  # Sunday at midnight
        'kwargs': {'days': 90},
        'options': {
            'expires': 3600,  # Task expires after 1 hour
        }
    },
}

app.conf.timezone = 'UTC'


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f'Request: {self.request!r}')
