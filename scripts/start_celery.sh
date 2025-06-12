#!/bin/bash

# Start Celery worker with multiple queues
celery -A notification_system worker \
    --loglevel=info \
    --queues=default,email,sms,push \
    --concurrency=4 \
    --max-tasks-per-child=1000
