"""
RSS Feed Scraper für News-Aggregation (Multi-Source kompatibel)
"""

import feedparser
import requests
from typing import Dict, List, Any
from datetime import datetime, timedelta
import logging
from urllib.parse import urljoin, urlparse

from .base_scraper import BaseScraper
from app.utils.timezone_utils import get_cet_time, parse_iso_to_cet

logger = logging.getLogger(__name__)


class RSSFeedScraper(BaseScraper):
    """Multi-Source-kompatibler RSS Feed Scraper"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.source_type = 'rss'
        self.url = config.get('url', '')
        self.max_articles = config.get('max_articles', 10)
        self.update_interval = config.get('update_interval', 30)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36'
        })
    
    def validate_config(self) -> bool:
        """Validiert die RSS-Feed-Konfiguration"""
        if not self.url:
            logger.error("RSS-URL ist erforderlich")
            return False
        
        try:
            # Test-Request für URL-Validierung
            response = self.session.head(self.url, timeout=10, allow_redirects=True)
            if response.status_code >= 400:
                logger.error(f"RSS-URL nicht erreichbar: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"RSS-URL-Validierung fehlgeschlagen: {e}")
            return False
        
        return True
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Scrapt Artikel aus dem RSS-Feed"""
        try:
            logger.info(f"🔄 Scraping RSS-Feed: {self.url}")
            
            # RSS-Feed abrufen
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()
            
            # Feed parsen
            feed = feedparser.parse(response.content)
            
            if not hasattr(feed, 'entries') or not feed.entries:
                logger.warning(f"Keine Einträge im RSS-Feed gefunden: {self.url}")
                return []
            
            articles = []
            for entry in feed.entries[:self.max_articles]:
                try:
                    # Basis-Artikel-Daten
                    article = {
                        'title': entry.get('title', 'Ohne Titel').strip(),
                        'link': entry.get('link', ''),
                        'description': entry.get('summary', entry.get('description', '')),
                        'published': self._parse_publish_date(entry),
                        'source': feed.feed.get('title', self.source_config.get('name', 'RSS Feed')),
                        'source_type': 'rss',
                        'source_url': self.url,
                        'tags': self._extract_tags(entry),
                        'content': entry.get('content', [{}])[0].get('value', ''),
                        'scraped_at': get_cet_time().isoformat()
                    }
                    
                    # Content-Hash für Duplikatserkennung
                    article = self.normalize_article(article)
                    articles.append(article)
                    
                except Exception as e:
                    logger.warning(f"Fehler beim Verarbeiten von RSS-Eintrag: {e}")
                    continue
            
            logger.info(f"✅ {len(articles)} Artikel aus RSS-Feed extrahiert: {self.url}")
            return articles
            
        except Exception as e:
            logger.error(f"❌ Fehler beim RSS-Scraping: {e}")
            return []
    
    def _parse_publish_date(self, entry) -> str:
        """Parst das Veröffentlichungsdatum aus dem RSS-Eintrag"""
        try:
            # Verschiedene Datum-Felder versuchen
            for date_field in ['published_parsed', 'updated_parsed']:
                if hasattr(entry, date_field) and getattr(entry, date_field):
                    time_struct = getattr(entry, date_field)
                    dt = datetime(*time_struct[:6])
                    return dt.isoformat()
            
            # String-Datum versuchen
            for date_field in ['published', 'updated']:
                if hasattr(entry, date_field):
                    date_str = getattr(entry, date_field)
                    if date_str:
                        # Einfache Parse-Versuche
                        for fmt in ['%a, %d %b %Y %H:%M:%S %z', '%Y-%m-%dT%H:%M:%S%z']:
                            try:
                                dt = datetime.strptime(date_str, fmt)
                                return dt.isoformat()
                            except:
                                continue
            
            # Fallback: aktueller Zeitstempel
            return get_cet_time().isoformat()
            
        except Exception as e:
            logger.debug(f"Datum-Parsing fehlgeschlagen: {e}")
            return get_cet_time().isoformat()
    
    def _extract_tags(self, entry) -> List[str]:
        """Extrahiert Tags aus dem RSS-Eintrag"""
        tags = []
        
        try:
            # RSS-Tags
            if hasattr(entry, 'tags') and entry.tags:
                for tag in entry.tags:
                    if hasattr(tag, 'term') and tag.term:
                        tags.append(tag.term.strip())
            
            # Kategorien
            if hasattr(entry, 'category') and entry.category:
                tags.append(entry.category.strip())
        
        except Exception as e:
            logger.debug(f"Tag-Extraktion fehlgeschlagen: {e}")
        
        return tags[:5]  # Maximal 5 Tags


class RSSNewsScraper:
    """Scraper für RSS-basierte News-Quellen"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36'
        })
    
    def get_default_sources(self) -> List[Dict[str, Any]]:
        """Standard RSS-Quellen für deutsche News"""
        return [
            {
                'name': 'Reitschuster.de',
                'url': 'https://reitschuster.de/feed/',
                'type': 'rss',
                'keywords': ['Corona', 'Politik', 'Kritik', 'Medien'],
                'category': 'alternative_media'
            },
            {
                'name': 'Tichys Einblick',
                'url': 'https://www.tichyseinblick.de/feed/',
                'type': 'rss',
                'keywords': ['Politik', 'Wirtschaft', 'Analyse'],
                'category': 'conservative'
            },
            {
                'name': 'Achse des Guten',
                'url': 'https://www.achgut.com/rss.xml',
                'type': 'rss',
                'keywords': ['Politik', 'Gesellschaft', 'Kommentar'],
                'category': 'opinion'
            },
            {
                'name': 'NachDenkSeiten',
                'url': 'https://www.nachdenkseiten.de/?feed=rss2',
                'type': 'rss',
                'keywords': ['Politik', 'Medien', 'Gesellschaft'],
                'category': 'left_alternative'
            },
            {
                'name': 'RT DE',
                'url': 'https://rtde.me/feeds/all/',
                'type': 'rss',
                'keywords': ['International', 'Politik', 'Wirtschaft'],
                'category': 'international'
            },
            {
                'name': 'Anti-Spiegel',
                'url': 'https://www.anti-spiegel.ru/feed/',
                'type': 'rss',
                'keywords': ['Geopolitik', 'Medien', 'Analyse'],
                'category': 'alternative_media'
            },
            {
                'name': 'Compact Online',
                'url': 'https://www.compact-online.de/feed/',
                'type': 'rss',
                'keywords': ['Politik', 'Gesellschaft', 'Deutschland'],
                'category': 'nationalist'
            },
            {
                'name': 'KenFM (Apolut)',
                'url': 'https://apolut.net/feed/',
                'type': 'rss',
                'keywords': ['Alternative', 'Aufklärung', 'Politik'],
                'category': 'alternative_media'
            },
            {
                'name': 'Telepolis',
                'url': 'https://www.telepolis.de/rss/news.xml',
                'type': 'rss',
                'keywords': ['Technologie', 'Politik', 'Gesellschaft'],
                'category': 'tech_politics'
            },
            {
                'name': 'Junge Freiheit',
                'url': 'https://jungefreiheit.de/feed/',
                'type': 'rss',
                'keywords': ['Politik', 'Kultur', 'Deutschland'],
                'category': 'conservative'
            }
        ]
    
    def add_rss_source(self, name: str, url: str, keywords: List[str] = None, 
                      category: str = 'general') -> str:
        """Fügt eine neue RSS-Quelle hinzu"""
        try:
            # Teste RSS-Feed
            feed = feedparser.parse(url)
            if feed.bozo and not feed.entries:
                raise ValueError(f"Ungültiger RSS-Feed: {url}")
            
            source_id = str(uuid.uuid4())
            source_data = {
                'id': source_id,
                'type': 'rss',
                'name': name,
                'url': url,
                'keywords': keywords or [],
                'category': category,
                'is_active': True,
                'last_updated': None,
                'last_article_count': 0,
                'total_articles_collected': 0,
                'added_at': datetime.now().isoformat(),
                'feed_info': {
                    'title': feed.feed.get('title', name),
                    'description': feed.feed.get('description', ''),
                    'language': feed.feed.get('language', 'de'),
                    'last_build_date': feed.feed.get('updated', '')
                }
            }
            
            # In JSON speichern
            sources = json_manager.read('sources')
            if 'rss' not in sources:
                sources['rss'] = {}
            
            sources['rss'][source_id] = source_data
            sources['metadata']['last_updated'] = datetime.now().isoformat()
            sources['metadata']['total_count'] = len(sources.get('telegram', {})) + len(sources.get('rss', {}))
            
            json_manager.write('sources', sources)
            
            logger.info(f"RSS-Quelle {name} hinzugefügt mit ID {source_id}")
            return source_id
            
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen der RSS-Quelle {name}: {e}")
            raise
    
    def scrape_rss_feed(self, source_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scraped Artikel aus einem RSS-Feed"""
        try:
            url = source_data['url']
            feed = feedparser.parse(url)
            
            articles = []
            
            for entry in feed.entries[:10]:  # Limitiere auf 10 neueste Artikel
                try:
                    # Basis-Artikel-Daten
                    article = {
                        'id': str(uuid.uuid4()),
                        'title': entry.get('title', 'Unbekannter Titel'),
                        'url': entry.get('link', ''),
                        'published_at': self._parse_date(entry.get('published', '')),
                        'source': source_data['name'],
                        'source_id': source_data['id'],
                        'source_type': 'rss',
                        'category': source_data.get('category', 'general'),
                        'scraped_at': datetime.now().isoformat()
                    }
                    
                    # Content extrahieren
                    content = ''
                    if hasattr(entry, 'content') and entry.content:
                        content = entry.content[0].value
                    elif hasattr(entry, 'summary'):
                        content = entry.summary
                    elif hasattr(entry, 'description'):
                        content = entry.description
                    
                    # HTML bereinigen
                    if content:
                        soup = BeautifulSoup(content, 'html.parser')
                        article['content'] = soup.get_text(strip=True)[:1000]  # Ersten 1000 Zeichen
                        article['summary'] = soup.get_text(strip=True)[:300]   # Ersten 300 Zeichen
                    
                    # Keywords extrahieren
                    article['keywords'] = self._extract_keywords(
                        article['title'] + ' ' + article.get('content', ''),
                        source_data.get('keywords', [])
                    )
                    
                    # Relevanz-Score (einfache Implementierung)
                    article['relevance_score'] = self._calculate_relevance_score(article)
                    
                    # Tags hinzufügen
                    if hasattr(entry, 'tags'):
                        article['tags'] = [tag.term for tag in entry.tags]
                    
                    articles.append(article)
                    
                except Exception as e:
                    logger.warning(f"Fehler beim Verarbeiten eines Artikels: {e}")
                    continue
            
            logger.info(f"RSS-Feed {source_data['name']}: {len(articles)} Artikel gefunden")
            return articles
            
        except Exception as e:
            logger.error(f"Fehler beim Scrapen des RSS-Feeds {source_data['name']}: {e}")
            return []
    
    def _parse_date(self, date_str: str) -> str:
        """Parst verschiedene Datumsformate"""
        if not date_str:
            return datetime.now().isoformat()
        
        try:
            # feedparser normalisiert bereits viele Formate
            import time
            timestamp = time.mktime(feedparser._parse_date(date_str))
            return datetime.fromtimestamp(timestamp).isoformat()
        except:
            return datetime.now().isoformat()
    
    def _extract_keywords(self, text: str, source_keywords: List[str]) -> List[str]:
        """Extrahiert Keywords aus dem Text"""
        keywords = set(source_keywords)  # Source Keywords als Basis
        
        # Wichtige deutsche Begriffe für News-Analyse
        important_terms = [
            'Corona', 'COVID', 'Impfung', 'Lockdown', 'Maßnahmen',
            'Politik', 'Regierung', 'Bundestag', 'Merkel', 'Scholz',
            'Ukraine', 'Russland', 'Krieg', 'Sanktionen', 'NATO',
            'Wirtschaft', 'Inflation', 'Euro', 'Energie', 'Gas',
            'Medien', 'Presse', 'Zensur', 'Meinungsfreiheit',
            'Deutschland', 'EU', 'Europa', 'Migration', 'Asyl',
            'Klima', 'Umwelt', 'Grüne', 'AfD', 'FDP', 'SPD', 'CDU',
            'Demonstration', 'Protest', 'Widerstand', 'Kritik'
        ]
        
        text_lower = text.lower()
        for term in important_terms:
            if term.lower() in text_lower:
                keywords.add(term)
        
        return list(keywords)[:10]  # Maximal 10 Keywords
    
    def _calculate_relevance_score(self, article: Dict[str, Any]) -> float:
        """Berechnet einen einfachen Relevanz-Score"""
        score = 0.5  # Basis-Score
        
        # Höhere Bewertung für bestimmte Keywords
        high_impact_terms = ['Corona', 'Impfung', 'Lockdown', 'Ukraine', 'Krieg', 'Wirtschaft']
        for term in high_impact_terms:
            if term in article.get('keywords', []):
                score += 0.1
        
        # Bewertung basierend auf Titel-Keywords
        title_words = article['title'].lower().split()
        if any(word in ['breaking', 'eilmeldung', 'exklusiv', 'skandal'] for word in title_words):
            score += 0.2
        
        return min(score, 1.0)  # Max 1.0


def sync_scrape_rss_feeds():
    """Synchrone Wrapper-Funktion für alle RSS-Feeds"""
    try:
        scraper = RSSNewsScraper()
        sources = json_manager.read('sources')
        
        total_new_articles = 0
        
        # RSS-Quellen verarbeiten
        for source_id, source_data in sources.get('rss', {}).items():
            if not source_data.get('is_active', True):
                continue
                
            articles = scraper.scrape_rss_feed(source_data)
            
            if articles:
                # Artikel speichern
                articles_data = json_manager.read('articles')
                
                for article in articles:
                    # Prüfe auf Duplikate (URL-basiert)
                    existing = any(
                        existing_article.get('url') == article['url']
                        for existing_article in articles_data.get('articles', {}).values()
                    )
                    
                    if not existing:
                        articles_data['articles'][article['id']] = article
                        total_new_articles += 1
                
                # Update Metadaten
                articles_data['metadata']['last_updated'] = datetime.now().isoformat()
                articles_data['metadata']['total_count'] = len(articles_data['articles'])
                
                json_manager.write('articles', articles_data)
                
                # Update Source-Statistiken
                source_data['last_updated'] = datetime.now().isoformat()
                source_data['last_article_count'] = len(articles)
                source_data['total_articles_collected'] += len(articles)
        
        # Sources speichern
        json_manager.write('sources', sources)
        
        logger.info(f"RSS-Scraping abgeschlossen: {total_new_articles} neue Artikel")
        return total_new_articles
        
    except Exception as e:
        logger.error(f"Fehler beim RSS-Scraping: {e}")
        return 0


# RSS-Quellen automatisch hinzufügen falls noch nicht vorhanden
def initialize_default_rss_sources():
    """Initialisiert Standard-RSS-Quellen"""
    try:
        scraper = RSSNewsScraper()
        sources = json_manager.read('sources')
        
        if 'rss' not in sources or not sources['rss']:
            logger.info("Initialisiere Standard-RSS-Quellen...")
            
            for source_config in scraper.get_default_sources():
                try:
                    scraper.add_rss_source(
                        name=source_config['name'],
                        url=source_config['url'],
                        keywords=source_config['keywords'],
                        category=source_config['category']
                    )
                except Exception as e:
                    logger.warning(f"Konnte RSS-Quelle {source_config['name']} nicht hinzufügen: {e}")
            
            logger.info("Standard-RSS-Quellen initialisiert")
        
    except Exception as e:
        logger.error(f"Fehler bei der RSS-Initialisierung: {e}")


if __name__ == "__main__":
    # Test der RSS-Funktionalität
    initialize_default_rss_sources()
    result = sync_scrape_rss_feeds()
    print(f"RSS-Test abgeschlossen: {result} Artikel gesammelt")
