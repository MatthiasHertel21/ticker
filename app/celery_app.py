"""
Celery Application Configuration
"""

from celery import Celery
import os

# Celery-App erstellen
celery_app = Celery('ticker')

# Konfiguration
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
