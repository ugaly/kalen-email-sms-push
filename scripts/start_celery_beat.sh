#!/bin/bash

# Start Celery Beat scheduler
celery -A notification_system beat \
    --loglevel=info \
    --scheduler=django_celery_beat.schedulers:DatabaseScheduler
