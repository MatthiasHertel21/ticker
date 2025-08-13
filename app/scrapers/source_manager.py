"""
Multi-Source News Scraper Manager
Koordiniert verschiedene Scraper-Typen und Duplikatserkennung
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

from app.data.json_manager import JSONManager
from app.utils.spam_detector import SpamDetector
from app.utils.timezone_utils import get_cet_time

# Scraper Imports
from .telegram_scraper_wrapper import TelethonScraper
from .rss_scraper import RSSFeedScraper
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class DuplicateDetector:
    """
    Cross-Source Duplikatserkennung
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
    
    def is_duplicate(self, new_article: Dict[str, Any], existing_articles: List[Dict[str, Any]]) -> Optional[str]:
        """
        Prüft ob Artikel bereits existiert
        
        Args:
            new_article: Neuer Artikel
            existing_articles: Liste existierender Artikel
            
        Returns:
            Optional[str]: ID des Duplikats oder None
        """
        new_hash = new_article.get('content_hash')
        new_title = new_article.get('title', '').lower().strip()
        new_content = new_article.get('content', '').lower().strip()[:200]
        
        for existing in existing_articles:
            # 1. Exakter Hash-Vergleich
            if new_hash and existing.get('content_hash') == new_hash:
                return existing.get('id')
            
            # 2. Titel-Ähnlichkeit
            existing_title = existing.get('title', '').lower().strip()
            if self._calculate_similarity(new_title, existing_title) > self.similarity_threshold:
                return existing.get('id')
            
            # 3. Content-Ähnlichkeit (erste 200 Zeichen)
            existing_content = existing.get('content', '').lower().strip()[:200]
            if new_content and existing_content:
                if self._calculate_similarity(new_content, existing_content) > self.similarity_threshold:
                    return existing.get('id')
        
        return None
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Berechnet Textähnlichkeit mit Levenshtein-Distanz"""
        if not text1 or not text2:
            return 0.0
            
        try:
            import Levenshtein
            distance = Levenshtein.distance(text1, text2)
            max_len = max(len(text1), len(text2))
            
            if max_len == 0:
                return 1.0
                
            similarity = 1.0 - (distance / max_len)
            return similarity
        except ImportError:
            # Fallback: einfacher String-Vergleich
            if text1 == text2:
                return 1.0
            elif text1 in text2 or text2 in text1:
                return 0.9
            else:
                return 0.0


class MultiSourceManager:
    """
    Manager für alle News-Quellen mit Duplikatserkennung
    """
    
    def __init__(self, data_dir: str = "/app/data"):
        self.json_manager = JSONManager(data_dir)
        self.spam_detector = SpamDetector()
        self.duplicate_detector = DuplicateDetector()
        
        # Scraper-Registry
        self.scraper_classes = {
            'telegram': TelethonScraper,
            'rss': RSSFeedScraper,
            # 'twitter': TwitterScraper,  # Später
            # 'web': WebScraper,         # Später
        }
        
        self.scrapers: List[BaseScraper] = []
        self._load_sources()
    
    def _load_sources(self):
        """Lädt und initialisiert alle konfigurierten Quellen"""
        try:
            sources_data = self.json_manager.read('sources')
            sources = sources_data.get('sources', [])
            
            self.scrapers = []
            
            changed = False  # ob wir die sources.json nachführen müssen (z.B. Cache Infos)
            now = get_cet_time()
            
            for source_config in sources:
                source_type = source_config.get('type')
                
                if source_type not in self.scraper_classes:
                    logger.warning(f"⚠️ Unbekannter Source-Type: {source_type}")
                    continue
                
                try:
                    scraper_class = self.scraper_classes[source_type]
                    scraper = scraper_class(source_config)
                    
                    # Validierungs-Caching: nicht bei jedem Request Netz-HEAD machen
                    # Cache-Felder: validation_status (bool), validated_at (ISO), validation_error
                    needs_validation = False
                    if source_type == 'rss':
                        validated_at = source_config.get('validated_at')
                        validation_status = source_config.get('validation_status')
                        # Revalidierung nur wenn nie validiert oder älter als 6 Stunden
                        if not validated_at:
                            needs_validation = True
                        else:
                            try:
                                from dateutil import parser
                                age = now - parser.isoparse(validated_at)
                                if age.total_seconds() > 6 * 3600:
                                    needs_validation = True
                            except Exception:
                                needs_validation = True
                    else:
                        # Telegram (und andere) sehr günstig -> einmalige Prüfung ok
                        validation_status = source_config.get('validation_status')
                        if validation_status is None:
                            needs_validation = True
                    
                    if needs_validation:
                        try:
                            if scraper.validate_config():
                                source_config['validation_status'] = True
                                source_config['validated_at'] = now.isoformat()
                                source_config.pop('validation_error', None)
                                logger.info(f"✅ Validierung OK: {scraper.source_name}")
                            else:
                                source_config['validation_status'] = False
                                source_config['validated_at'] = now.isoformat()
                                source_config['validation_error'] = 'Konfiguration ungültig'
                                logger.warning(f"⚠️ Validierung fehlgeschlagen: {scraper.source_name}")
                            changed = True
                        except Exception as ve:
                            source_config['validation_status'] = False
                            source_config['validated_at'] = now.isoformat()
                            source_config['validation_error'] = str(ve)
                            changed = True
                            logger.error(f"❌ Validierungsfehler {scraper.source_name}: {ve}")
                    else:
                        # Skip erneute Validierung – vertraue Cache
                        if not source_config.get('validation_status', True):
                            logger.warning(f"⚠️ Verwende gecachten ungültigen Status: {scraper.source_name}")
                        else:
                            logger.debug(f"⏩ Überspringe Revalidierung (Cache frisch): {scraper.source_name}")
                    
                    # Scraper immer hinzufügen (auch wenn aktuell invalid), damit UI Status anzeigen kann
                    self.scrapers.append(scraper)
                except Exception as e:
                    logger.error(f"❌ Fehler beim Initialisieren von {source_config.get('name', 'Unknown')}: {e}")
                    continue
            
            if changed:
                # Persistiere aktualisierte Cache-Felder
                try:
                    sources_data['sources'] = sources
                    self.json_manager.write('sources', sources_data, backup=False)
                except Exception as e:
                    logger.error(f"Konnte Validierungs-Cache nicht speichern: {e}")
                    
            logger.info(f"📊 {len(self.scrapers)} Scraper initialisiert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Quellen: {e}")
            self.scrapers = []
    
    def scrape_all_sources(self, max_workers: int = 3) -> Dict[str, Any]:
        """
        Scrapt alle konfigurierten Quellen parallel
        
        Args:
            max_workers: Maximale Anzahl paralleler Worker
            
        Returns:
            Dict: Scraping-Ergebnisse und Statistiken
        """
        if not self.scrapers:
            logger.warning("Keine Scraper konfiguriert")
            return {'total_articles': 0, 'new_articles': 0, 'duplicates': 0, 'spam': 0}
        
        logger.info(f"🚀 Starte Multi-Source-Scraping mit {len(self.scrapers)} Scrapern")
        
        # Bestehende Artikel für Duplikatserkennung laden
        existing_articles = self._load_existing_articles()
        
        all_new_articles = []
        source_stats = {}
        
        # Parallel scraping
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_scraper = {
                executor.submit(scraper.scrape): scraper 
                for scraper in self.scrapers if scraper.enabled
            }
            
            for future in as_completed(future_to_scraper):
                scraper = future_to_scraper[future]
                
                try:
                    articles = future.result(timeout=300)  # 5 Minuten Timeout
                    
                    source_stats[scraper.source_name] = {
                        'scraped_articles': len(articles),
                        'source_type': scraper.source_type,
                        'errors': 0
                    }
                    
                    all_new_articles.extend(articles)
                    logger.info(f"✅ {scraper.source_name}: {len(articles)} Artikel")
                    
                except Exception as e:
                    logger.error(f"❌ {scraper.source_name}: Scraping fehlgeschlagen - {e}")
                    source_stats[scraper.source_name] = {
                        'scraped_articles': 0,
                        'source_type': scraper.source_type,
                        'errors': 1
                    }
        
        # Duplikate filtern und Spam erkennen
        processing_stats = self._process_articles(all_new_articles, existing_articles)
        
        # Statistiken zusammenfassen
        total_stats = {
            'total_articles': len(all_new_articles),
            'new_articles': processing_stats['new_articles'],
            'duplicates': processing_stats['duplicates'],
            'spam': processing_stats['spam'],
            'sources': source_stats,
            'timestamp': get_cet_time().isoformat()
        }
        
        logger.info(f"📊 Scraping abgeschlossen: {total_stats['new_articles']} neue Artikel, "
                   f"{total_stats['duplicates']} Duplikate, {total_stats['spam']} Spam")
        
        return total_stats
    
    def _load_existing_articles(self) -> List[Dict[str, Any]]:
        """Lädt bestehende Artikel für Duplikatserkennung"""
        try:
            articles_data = self.json_manager.read('articles')
            return articles_data.get('articles', [])
        except Exception as e:
            logger.error(f"Fehler beim Laden bestehender Artikel: {e}")
            return []
    
    def _process_articles(self, new_articles: List[Dict[str, Any]], 
                         existing_articles: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Verarbeitet neue Artikel: Duplikatserkennung, Spam-Filterung, Speicherung
        """
        stats = {'new_articles': 0, 'duplicates': 0, 'spam': 0}
        
        articles_to_save = []
        
        for article in new_articles:
            # 1. Duplikatserkennung
            duplicate_id = self.duplicate_detector.is_duplicate(article, existing_articles)
            if duplicate_id:
                logger.debug(f"Duplikat erkannt: {article.get('title', '')} -> {duplicate_id}")
                stats['duplicates'] += 1
                continue
            
            # 2. Spam-Erkennung
            spam_result = self.spam_detector.is_spam(article)
            if spam_result['is_spam']:
                article['relevance_score'] = 'spam'
                article['spam_reason'] = spam_result['reason']
                article['rated_at'] = get_cet_time().isoformat()
                stats['spam'] += 1
                logger.debug(f"Spam erkannt: {article.get('title', '')} - {spam_result['reason']}")
            
            # 3. Artikel zur Speicherung hinzufügen
            articles_to_save.append(article)
            stats['new_articles'] += 1
        
        # 4. Neue Artikel speichern
        if articles_to_save:
            self._save_new_articles(articles_to_save)
        
        return stats
    
    def _save_new_articles(self, articles: List[Dict[str, Any]]):
        """Speichert neue Artikel in JSON"""
        try:
            articles_data = self.json_manager.read('articles')
            existing_articles = articles_data.get('articles', [])
            
            # Neue Artikel hinzufügen
            existing_articles.extend(articles)
            
            # Nach Datum sortieren (neueste zuerst)
            existing_articles.sort(
                key=lambda x: x.get('published_date', ''), 
                reverse=True
            )
            
            # Artikel-Limit prüfen (z.B. max 1000 Artikel)
            max_articles = 1000
            if len(existing_articles) > max_articles:
                existing_articles = existing_articles[:max_articles]
                logger.info(f"Artikel-Liste auf {max_articles} Artikel begrenzt")
            
            # Speichern
            articles_data['articles'] = existing_articles
            articles_data['last_updated'] = get_cet_time().isoformat()
            
            self.json_manager.write('articles', articles_data)
            logger.info(f"💾 {len(articles)} neue Artikel gespeichert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Artikel: {e}")
    
    def get_source_stats(self) -> Dict[str, Any]:
        """Gibt Statistiken aller konfigurierten Quellen zurück"""
        stats = {
            'total_sources': len(self.scrapers),
            'active_sources': len([s for s in self.scrapers if s.enabled]),
            'sources': []
        }
        
        for scraper in self.scrapers:
            scraper_stats = scraper.get_scraping_stats()
            stats['sources'].append(scraper_stats)
        
        return stats
    
    def add_source(self, source_config: Dict[str, Any]) -> bool:
        """Fügt neue Quelle hinzu"""
        try:
            # Validierung
            required_fields = ['name', 'type', 'enabled']
            for field in required_fields:
                if field not in source_config:
                    logger.error(f"Pflichtfeld fehlt: {field}")
                    return False
            
            # Zu sources.json hinzufügen
            sources_data = self.json_manager.read('sources')
            sources = sources_data.get('sources', [])
            
            # Duplikat prüfen
            existing_names = [s.get('name') for s in sources]
            if source_config['name'] in existing_names:
                logger.error(f"Quelle bereits vorhanden: {source_config['name']}")
                return False
            
            sources.append(source_config)
            sources_data['sources'] = sources
            
            self.json_manager.write('sources', sources_data)
            
            # Scraper neu laden
            self._load_sources()
            
            logger.info(f"✅ Neue Quelle hinzugefügt: {source_config['name']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Hinzufügen der Quelle: {e}")
            return False
