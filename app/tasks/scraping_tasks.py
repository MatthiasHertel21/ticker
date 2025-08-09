"""
Celery Tasks für Background-Verarbeitung
"""

from app.celery_app import celery_app
from celery.schedules import crontab
import os
import logging
from datetime import datetime
from app.scrapers import sync_monitor_telegram_channels, TelethonChannelScraper

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@celery_app.task(name='app.tasks.scraping_tasks.monitor_telegram_task')
def monitor_telegram_task():
    """Celery-Task für Telegram-Channel-Monitoring (Bot API - Legacy)"""
    try:
        logger.info("Starte Telegram-Channel-Monitoring (Bot API)")
        new_articles = sync_monitor_telegram_channels()
        logger.info(f"Bot API Monitoring abgeschlossen: {new_articles} neue Artikel")
        return {'new_articles': new_articles, 'status': 'success', 'scraper': 'bot_api'}
    except Exception as e:
        logger.error(f"Fehler beim Bot API Monitoring: {e}")
        return {'error': str(e), 'status': 'error', 'scraper': 'bot_api'}


@celery_app.task(name='app.tasks.scraping_tasks.monitor_telethon_task')
def monitor_telethon_task():
    """Celery-Task für Telethon-basiertes Telegram-Monitoring"""
    try:
        logger.info("Starte Telethon-Channel-Monitoring")
        
        # Prüfe ob Telethon-Session existiert
        session_path = '/app/data/telethon_session.session'
        if not os.path.exists(session_path):
            logger.warning("Telethon-Session nicht gefunden. Nutze Bot API als Fallback.")
            return monitor_telegram_task()
        
        # Verwende Telethon-Scraper
        scraper = TelethonChannelScraper()
        new_articles = scraper.scrape_channels()
        
        logger.info(f"Telethon-Monitoring abgeschlossen: {new_articles} neue Artikel")
        return {'new_articles': new_articles, 'status': 'success', 'scraper': 'telethon'}
        
    except Exception as e:
        logger.error(f"Fehler beim Telethon-Monitoring: {e}")
        logger.info("Fallback zu Bot API")
        return monitor_telegram_task()


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


# Periodische Tasks konfigurieren
celery_app.conf.beat_schedule = {
    'monitor-telegram-channels': {
        'task': 'app.tasks.scraping_tasks.monitor_telethon_task',  # Aktualisiert zu Telethon
        'schedule': crontab(minute='*/30'),  # Alle 30 Minuten
    },
    'monitor-telegram-bot-fallback': {
        'task': 'app.tasks.scraping_tasks.monitor_telegram_task',  # Bot API als Backup
        'schedule': crontab(minute='*/60'),  # Jede Stunde als Fallback
    },
    'cleanup-old-articles': {
        'task': 'app.tasks.scraping_tasks.cleanup_old_articles_task',
        'schedule': crontab(hour=2, minute=0),  # Täglich um 2:00 Uhr
    },
}
