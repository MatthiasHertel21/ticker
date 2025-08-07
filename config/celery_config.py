"""
Celery-Konfiguration für News-Aggregator
"""

import os
from celery import Celery

def make_celery(app_name='ticker'):
    """Celery-App Factory"""
    
    celery = Celery(
        app_name,
        broker=os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0'),
        backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0'),
        include=['app.tasks.scraping_tasks']
    )
    
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='Europe/Berlin',
        enable_utc=True,
        
        # Worker-Konfiguration
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        
        # Task-Routing
        task_routes={
            'app.tasks.scraping_tasks.*': {'queue': 'scraping'},
        },
        
        # Periodische Tasks
        beat_schedule={
            'monitor-telegram-channels': {
                'task': 'app.tasks.scraping_tasks.monitor_telegram_task',
                'schedule': 30.0 * 60,  # 30 Minuten in Sekunden
            },
            'cleanup-old-articles': {
                'task': 'app.tasks.scraping_tasks.cleanup_old_articles_task',
                'schedule': 24.0 * 60 * 60,  # 24 Stunden in Sekunden
            },
        },
    )
    
    return celery
