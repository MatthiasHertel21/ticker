"""
Telethon Scraper Wrapper für Multi-Source-Integration
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base_scraper import BaseScraper
from .telethon_scraper import TelethonChannelScraper
from app.utils.timezone_utils import get_cet_time

logger = logging.getLogger(__name__)


class TelethonScraper(BaseScraper):
    """
    Wrapper für den bestehenden TelethonChannelScraper
    Macht ihn kompatibel mit der neuen Multi-Source-Architektur
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.source_type = 'telegram'
        
        # Support both direct config and nested config structure
        if 'config' in config and isinstance(config['config'], dict):
            # New structure: config.config.channel_username
            telegram_config = config['config']
            self.channel_username = telegram_config.get('channel_username', '')
            self.max_messages = telegram_config.get('max_messages', 10)
        else:
            # Legacy structure: config.channel_username
            self.channel_username = config.get('channel_username', '')
            self.max_messages = config.get('max_messages', 10)
        
        # Initialisiere den ursprünglichen Scraper
        self.telethon_scraper = TelethonChannelScraper()
    
    def validate_config(self) -> bool:
        """Validiert die Telegram-spezifische Konfiguration"""
        if not self.channel_username:
            logger.error("Channel-Username ist erforderlich")
            return False
        
        # Prüfe ob Telethon-Session existiert
        import os
        session_path = '/app/data/telethon_session.session'
        if not os.path.exists(session_path):
            logger.warning("Telethon-Session nicht gefunden - benötigt Setup")
            return False
        
        return True
    
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrapt Nachrichten aus dem konfigurierten Telegram-Channel
        """
        try:
            logger.info(f"Scraping Telegram-Channel: {self.channel_username}")
            
            # Nutze den bestehenden Telethon-Scraper
            # Da er alle konfigurierten Channels scrapt, filtern wir später
            raw_articles = self.telethon_scraper.scrape_channels()
            
            # Konvertiere die Artikel ins neue Format
            normalized_articles = []
            
            for article_data in raw_articles:
                try:
                    # Artikel normalisieren
                    normalized_article = self.normalize_article(article_data)
                    normalized_articles.append(normalized_article)
                    
                except Exception as e:
                    logger.error(f"Fehler beim Normalisieren des Artikels: {e}")
                    continue
            
            logger.info(f"✅ {len(normalized_articles)} Artikel aus Telegram gescrapt")
            
            # Update stats
            self.last_scrape_time = get_cet_time().isoformat()
            self.last_article_count = len(normalized_articles)
            self.last_error = None
            
            return normalized_articles
            
        except Exception as e:
            error_msg = f"Fehler beim Telegram-Scraping: {e}"
            logger.error(error_msg)
            self.last_error = str(e)
            self.last_scrape_time = get_cet_time().isoformat()
            self.last_article_count = 0
            return []
    
    def normalize_article(self, raw_article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalisiert Telegram-Artikel ins einheitliche Format
        """
        # Der TelethonChannelScraper gibt bereits normalisierte Artikel zurück
        # Wir müssen nur die Multi-Source-Felder hinzufügen
        
        normalized = raw_article.copy()
        
        # Multi-Source-Felder hinzufügen
        normalized['source_type'] = self.source_type
        normalized['source_name'] = self.source_name
        
        # Content-Hash für Duplikatserkennung generieren
        normalized['content_hash'] = self.generate_content_hash(normalized)
        
        # Ensure required fields exist
        if 'scraped_at' not in normalized:
            normalized['scraped_at'] = get_cet_time().isoformat()
        
        if 'published_date' not in normalized:
            normalized['published_date'] = normalized.get('scraped_at', get_cet_time().isoformat())
        
        return normalized
    
    def get_scraping_stats(self) -> Dict[str, Any]:
        """Gibt Scraping-Statistiken zurück"""
        stats = super().get_scraping_stats()
        
        # Telegram-spezifische Stats hinzufügen
        stats.update({
            'channel_username': self.channel_username,
            'max_messages': self.max_messages,
            'telethon_session_exists': self._check_telethon_session()
        })
        
        return stats
    
    def _check_telethon_session(self) -> bool:
        """Prüft ob Telethon-Session vorhanden ist"""
        import os
        session_path = '/app/data/telethon_session.session'
        return os.path.exists(session_path)
