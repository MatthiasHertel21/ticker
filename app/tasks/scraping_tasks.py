"""
Celery Tasks für Background-Verarbeitung mit Multi-Source-Support
"""

from app.celery_app import celery_app
try:
    from celery.schedules import crontab
    CELERY_AVAILABLE = celery_app is not None
except ImportError:
    CELERY_AVAILABLE = False
    crontab = None

import os
import logging
from datetime import datetime
try:
    from app.scrapers import sync_monitor_telegram_channels
except ImportError:
    sync_monitor_telegram_channels = None

try:
    from app.scrapers.telethon_scraper import TelethonChannelScraper
except ImportError:
    TelethonChannelScraper = None

from app.scrapers.source_manager import MultiSourceManager

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


@celery_app.task(name='app.tasks.scraping_tasks.multi_source_scraping_task')
def multi_source_scraping_task():
    """Celery-Task für Multi-Source-Scraping aller konfigurierten Quellen"""
    try:
        logger.info("🚀 Starte Multi-Source-Scraping")
        
        # Multi-Source-Manager initialisieren
        source_manager = MultiSourceManager()
        
        # Alle Quellen scrapen
        results = source_manager.scrape_all_sources(max_workers=3)
        
        logger.info(f"📊 Multi-Source-Scraping abgeschlossen: "
                   f"{results['new_articles']} neue Artikel, "
                   f"{results['duplicates']} Duplikate, "
                   f"{results['spam']} Spam")
        
        return {
            'status': 'success',
            'scraper': 'multi_source',
            **results
        }
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Multi-Source-Scraping: {e}")
        return {'error': str(e), 'status': 'error', 'scraper': 'multi_source'}


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
    'multi-source-scraping': {
        'task': 'app.tasks.scraping_tasks.multi_source_scraping_task',
        'schedule': crontab(minute='*/15'),  # Alle 15 Minuten Multi-Source-Scraping
    },
    'monitor-telegram-telethon': {
        'task': 'app.tasks.scraping_tasks.monitor_telethon_task',
        'schedule': crontab(minute='*/30'),  # Alle 30 Minuten Telethon (als Backup)
    },
    'monitor-telegram-bot-fallback': {
        'task': 'app.tasks.scraping_tasks.monitor_telegram_task',
        'schedule': crontab(minute='*/60'),  # Jede Stunde Bot API (Legacy-Fallback)
    },
    'cleanup-old-articles': {
        'task': 'app.tasks.scraping_tasks.cleanup_old_articles_task',
        'schedule': crontab(hour=2, minute=0),  # Täglich um 2:00 Uhr
    },
}
