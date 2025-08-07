"""
Celery Tasks für Background-Verarbeitung
"""

from celery import Celery
from celery.schedules import crontab
import os
import logging
from app.scrapers import sync_monitor_telegram_channels

# Celery-App erstellen
celery_app = Celery('ticker')

# Konfiguration laden
celery_app.conf.update(
    broker_url=os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Periodische Tasks
    beat_schedule={
        'monitor-telegram-channels': {
            'task': 'app.tasks.scraping_tasks.monitor_telegram_task',
            'schedule': crontab(minute='*/30'),  # Alle 30 Minuten
        },
        'cleanup-old-articles': {
            'task': 'app.tasks.scraping_tasks.cleanup_old_articles_task',
            'schedule': crontab(hour=2, minute=0),  # Täglich um 2:00 Uhr
        },
    },
)

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@celery_app.task(name='app.tasks.scraping_tasks.monitor_telegram_task')
def monitor_telegram_task():
    """Celery-Task für Telegram-Channel-Monitoring"""
    try:
        logger.info("Starte Telegram-Channel-Monitoring")
        new_articles = sync_monitor_telegram_channels()
        logger.info(f"Telegram-Monitoring abgeschlossen: {new_articles} neue Artikel")
        return {'new_articles': new_articles, 'status': 'success'}
    except Exception as e:
        logger.error(f"Fehler beim Telegram-Monitoring: {e}")
        return {'error': str(e), 'status': 'error'}


@celery_app.task(name='app.tasks.scraping_tasks.cleanup_old_articles_task')
def cleanup_old_articles_task():
    """Celery-Task für Cleanup alter Artikel"""
    try:
        from datetime import datetime, timedelta
        from app.data import json_manager
        
        logger.info("Starte Cleanup alter Artikel")
        
        # Artikel älter als 30 Tage löschen
        cutoff_date = datetime.now() - timedelta(days=30)
        articles = json_manager.read('articles')
        
        deleted_count = 0
        for article_id, article_data in list(articles.get('articles', {}).items()):
            scraped_at = datetime.fromisoformat(article_data.get('scraped_at', ''))
            if scraped_at < cutoff_date:
                json_manager.delete_item('articles', article_id)
                deleted_count += 1
        
        logger.info(f"Cleanup abgeschlossen: {deleted_count} alte Artikel gelöscht")
        return {'deleted_articles': deleted_count, 'status': 'success'}
    
    except Exception as e:
        logger.error(f"Fehler beim Cleanup: {e}")
        return {'error': str(e), 'status': 'error'}


@celery_app.task(name='app.tasks.scraping_tasks.process_article_with_ai')
def process_article_with_ai(article_id: str):
    """Celery-Task für KI-Verarbeitung von Artikeln (später implementiert)"""
    try:
        logger.info(f"KI-Verarbeitung für Artikel {article_id} gestartet")
        # TODO: OpenAI-Integration implementieren
        # - Relevanz-Score berechnen
        # - Sentiment-Analyse
        # - Automatisches Tagging
        
        logger.info(f"KI-Verarbeitung für Artikel {article_id} abgeschlossen")
        return {'article_id': article_id, 'status': 'success'}
        
    except Exception as e:
        logger.error(f"Fehler bei KI-Verarbeitung von Artikel {article_id}: {e}")
        return {'error': str(e), 'status': 'error'}


# Health-Check Task
@celery_app.task(name='app.tasks.scraping_tasks.health_check')
def health_check():
    """Celery Health-Check"""
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}
