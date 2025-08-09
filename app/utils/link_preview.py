"""
Link Preview Generator
Erstellt automatisch Previews für URLs in Artikeln
"""

import requests
from bs4 import BeautifulSoup
import re
import logging
from urllib.parse import urljoin, urlparse
import time

logger = logging.getLogger(__name__)

class LinkPreviewGenerator:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.timeout = 10
        self.max_content_length = 5 * 1024 * 1024  # 5MB max

    def extract_urls_from_text(self, text):
        """Extrahiert alle URLs aus einem Text"""
        if not text:
            return []
        
        # URL Pattern (http/https)
        url_pattern = r'https?://[^\s<>"]+[^\s<>".,;!?]'
        urls = re.findall(url_pattern, text, re.IGNORECASE)
        
        # Entferne Duplikate und bereinige
        unique_urls = []
        for url in urls:
            # Entferne häufige Trailing-Zeichen
            url = url.rstrip('.,;!?)')
            if url not in unique_urls:
                unique_urls.append(url)
        
        return unique_urls

    def fetch_page_info(self, url):
        """Holt Meta-Informationen einer Webseite"""
        try:
            # Prüfe Content-Length vor Download
            head_response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            content_length = head_response.headers.get('content-length')
            
            if content_length and int(content_length) > self.max_content_length:
                logger.warning(f"Seite zu groß: {url} ({content_length} bytes)")
                return None
            
            # Lade Seite
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extrahiere Meta-Informationen
            preview_data = {
                'url': response.url,  # Final URL nach Redirects
                'title': self._extract_title(soup),
                'description': self._extract_description(soup),
                'image': self._extract_image(soup, response.url),
                'site_name': self._extract_site_name(soup),
                'favicon': self._extract_favicon(soup, response.url)
            }
            
            return preview_data
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Fehler beim Laden von {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unerwarteter Fehler bei {url}: {e}")
            return None

    def _extract_title(self, soup):
        """Extrahiert den Titel der Seite"""
        # OpenGraph
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content'].strip()
        
        # Twitter Card
        twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
        if twitter_title and twitter_title.get('content'):
            return twitter_title['content'].strip()
        
        # Standard Title Tag
        title_tag = soup.find('title')
        if title_tag and title_tag.text:
            return title_tag.text.strip()
        
        return None

    def _extract_description(self, soup):
        """Extrahiert die Beschreibung der Seite"""
        # OpenGraph
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        
        # Twitter Card
        twitter_desc = soup.find('meta', attrs={'name': 'twitter:description'})
        if twitter_desc and twitter_desc.get('content'):
            return twitter_desc['content'].strip()
        
        # Standard Meta Description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        return None

    def _extract_image(self, soup, base_url):
        """Extrahiert das Haupt-Bild der Seite"""
        # OpenGraph
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return urljoin(base_url, og_image['content'])
        
        # Twitter Card
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        if twitter_image and twitter_image.get('content'):
            return urljoin(base_url, twitter_image['content'])
        
        return None

    def _extract_site_name(self, soup):
        """Extrahiert den Site-Namen"""
        og_site = soup.find('meta', property='og:site_name')
        if og_site and og_site.get('content'):
            return og_site['content'].strip()
        
        return None

    def _extract_favicon(self, soup, base_url):
        """Extrahiert das Favicon"""
        # Icon Links
        icon_link = soup.find('link', rel=lambda x: x and 'icon' in x.lower())
        if icon_link and icon_link.get('href'):
            return urljoin(base_url, icon_link['href'])
        
        # Standard Favicon
        return urljoin(base_url, '/favicon.ico')

    def generate_previews_for_article(self, article_content):
        """Generiert Link-Previews für alle URLs in einem Artikel"""
        if not article_content:
            return []
        
        urls = self.extract_urls_from_text(article_content)
        previews = []
        
        for url in urls[:3]:  # Maximal 3 Previews pro Artikel
            preview = self.fetch_page_info(url)
            if preview:
                previews.append(preview)
            time.sleep(0.5)  # Rate limiting
        
        return previews


# Global instance
link_preview_generator = LinkPreviewGenerator()

def get_link_previews(content):
    """Helper function für Templates"""
    return link_preview_generator.generate_previews_for_article(content)
