"""
Celery Application Configuration
"""

try:
    from celery import Celery
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    Celery = None

import os

# Celery-App erstellen
if CELERY_AVAILABLE:
    celery_app = Celery('ticker')
else:
    celery_app = None

# Konfiguration
if CELERY_AVAILABLE and celery_app:
    celery_app.conf.update(
        broker_url=os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0'),
        result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0'),
        task_serializer='json',
        accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    include=['app.tasks.scraping_tasks']
)

if __name__ == '__main__':
    celery_app.start()
