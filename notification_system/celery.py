import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notification_system.settings')

app = Celery('notification_system')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Configuration
app.conf.beat_schedule = {
    'process-pending-notifications': {
        'task': 'apps.notifications.tasks.process_pending_notifications',
        'schedule': 30.0,  # Run every 30 seconds (umnaweza adjust as unavotaka)
    },
    'cleanup-old-notifications': {
        'task': 'apps.notifications.tasks.cleanup_old_notifications',
        'schedule': 3600.0,  # kila lisaa limoja
    },
    'generate-notification-reports': {
        'task': 'apps.notifications.tasks.generate_notification_reports',
        'schedule': 86400.0,  # Run daily
    },
}

app.conf.task_routes = {
    'apps.notifications.tasks.send_email_notification': {'queue': 'email'},
    'apps.notifications.tasks.send_sms_notification': {'queue': 'sms'},
    'apps.notifications.tasks.send_push_notification': {'queue': 'push'},
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
