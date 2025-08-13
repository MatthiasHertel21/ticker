"""
Base Scraper Class für Multi-Source News Aggregation
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from app.utils.timezone_utils import get_cet_time

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Abstract Base Class für alle News-Scraper
    """
    
    def __init__(self, source_config: Dict[str, Any]):
        self.source_config = source_config
        self.source_type = source_config.get('type', 'unknown')
        self.source_name = source_config.get('name', 'Unknown Source')
        self.enabled = source_config.get('enabled', True)
        
    @abstractmethod
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Haupt-Scraping-Methode - muss von jeder Scraper-Klasse implementiert werden
        
        Returns:
            List[Dict]: Liste von Artikeln im standardisierten Format
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validiert die Scraper-Konfiguration
        
        Returns:
            bool: True wenn Konfiguration valide ist
        """
        pass
    
    def normalize_article(self, raw_article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalisiert Artikel-Daten in standardisiertes Format
        
        Args:
            raw_article: Rohe Artikel-Daten vom spezifischen Scraper
            
        Returns:
            Dict: Standardisierter Artikel
        """
        current_time = get_cet_time()
        
        normalized = {
            'id': self._generate_article_id(raw_article),
            'title': raw_article.get('title', '').strip(),
            'content': raw_article.get('content', '').strip(),
            'full_text': raw_article.get('full_text', raw_article.get('content', '')).strip(),
            'source': f"{self.source_type.title()} - {self.source_name}",
            'platform': self.source_type,
            'url': raw_article.get('url', ''),
            'published_date': self._parse_date(raw_article.get('published_date')),
            'scraped_date': current_time.isoformat(),
            'media': self._normalize_media(raw_article.get('media', {})),
            'links': raw_article.get('links', []),
            'tags': raw_article.get('tags', []),
            'author': raw_article.get('author', ''),
            'relevance_score': None,  # Wird später von Spam-Detector gesetzt
            'content_hash': self._generate_content_hash(raw_article),
        }
        
        # Source-spezifische Felder
        if self.source_type == 'telegram':
            normalized.update({
                'channel': raw_article.get('channel', ''),
                'message_id': raw_article.get('message_id'),
                'message_age': raw_article.get('message_age', 'unknown')
            })
        elif self.source_type == 'rss':
            normalized.update({
                'feed_url': raw_article.get('feed_url', ''),
                'categories': raw_article.get('categories', [])
            })
        elif self.source_type == 'twitter':
            normalized.update({
                'tweet_id': raw_article.get('tweet_id'),
                'username': raw_article.get('username', ''),
                'retweet_count': raw_article.get('retweet_count', 0),
                'like_count': raw_article.get('like_count', 0)
            })
        elif self.source_type == 'web':
            normalized.update({
                'domain': raw_article.get('domain', ''),
                'article_url': raw_article.get('article_url', ''),
                'publish_date': raw_article.get('publish_date')
            })
            
        return normalized
    
    def _generate_article_id(self, article: Dict[str, Any]) -> str:
        """Generiert eindeutige Artikel-ID basierend auf Source-Type"""
        if self.source_type == 'telegram':
            channel = article.get('channel', 'unknown')
            msg_id = article.get('message_id', 'unknown')
            return f"telegram_{channel}_{msg_id}"
        elif self.source_type == 'rss':
            url = article.get('url', '')
            if url:
                return f"rss_{hash(url)}"
            return f"rss_{hash(article.get('title', '') + str(article.get('published_date', '')))}"
        elif self.source_type == 'twitter':
            return f"twitter_{article.get('tweet_id', 'unknown')}"
        elif self.source_type == 'web':
            url = article.get('url', '')
            if url:
                return f"web_{hash(url)}"
            return f"web_{hash(article.get('title', '') + str(article.get('published_date', '')))}"
        else:
            return f"{self.source_type}_{hash(str(article))}"
    
    def _parse_date(self, date_value: Any) -> str:
        """Parst Datum in ISO-Format"""
        if isinstance(date_value, datetime):
            return date_value.isoformat()
        elif isinstance(date_value, str):
            try:
                # Versuche verschiedene Formate zu parsen
                from dateutil import parser
                parsed_date = parser.parse(date_value)
                return parsed_date.isoformat()
            except:
                logger.warning(f"Could not parse date: {date_value}")
                return get_cet_time().isoformat()
        else:
            return get_cet_time().isoformat()
    
    def _normalize_media(self, media: Dict[str, Any]) -> Dict[str, Any]:
        """Normalisiert Media-Daten"""
        return {
            'has_media': bool(media.get('images') or media.get('videos') or media.get('documents')),
            'media_type': media.get('media_type', 'none'),
            'images': media.get('images', []),
            'videos': media.get('videos', []),
            'documents': media.get('documents', [])
        }
    
    def _generate_content_hash(self, article: Dict[str, Any]) -> str:
        """Generiert Hash für Duplikatserkennung"""
        import hashlib
        
        # Verwende Titel + erste 200 Zeichen des Inhalts
        title = article.get('title', '').strip().lower()
        content = article.get('content', '').strip().lower()[:200]
        
        hash_input = f"{title}|{content}"
        return hashlib.md5(hash_input.encode('utf-8')).hexdigest()
    
    def get_scraping_stats(self) -> Dict[str, Any]:
        """Gibt Scraping-Statistiken zurück"""
        return {
            'source_type': self.source_type,
            'source_name': self.source_name,
            'enabled': self.enabled,
            'last_scrape': None,  # Wird von konkreten Implementierungen überschrieben
            'total_articles': 0,
            'errors': 0
        }
