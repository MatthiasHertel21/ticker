"""
oEmbed Preview Generator - Deutlich schneller als HTML Parsing
"""

import requests
import json
import logging
from urllib.parse import urlparse, quote
import re

logger = logging.getLogger(__name__)

class OEmbedPreviewGenerator:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; NewsBot/1.0)'
        })
        self.timeout = 3  # Viel schneller als 10s
        
        # oEmbed Endpoints für große Plattformen
        self.oembed_providers = {
            'youtube.com': 'https://www.youtube.com/oembed',
            'youtu.be': 'https://www.youtube.com/oembed',
            'twitter.com': 'https://publish.twitter.com/oembed',
            'x.com': 'https://publish.twitter.com/oembed',
            'instagram.com': 'https://graph.facebook.com/v8.0/instagram_oembed',
            'vimeo.com': 'https://vimeo.com/api/oembed.json',
            'soundcloud.com': 'https://soundcloud.com/oembed',
            'spotify.com': 'https://open.spotify.com/oembed',
            'tiktok.com': 'https://www.tiktok.com/oembed',
            'reddit.com': 'https://www.reddit.com/oembed',
            'slideshare.net': 'https://www.slideshare.net/api/oembed/2',
            'flickr.com': 'https://www.flickr.com/services/oembed',
        }

    def extract_urls_from_text(self, text):
        """Extrahiert URLs aus Text"""
        if not text:
            return []
        
        url_pattern = r'https?://[^\s<>"]+[^\s<>".,;!?]'
        urls = re.findall(url_pattern, text, re.IGNORECASE)
        
        unique_urls = []
        for url in urls:
            url = url.rstrip('.,;!?)')
            if url not in unique_urls:
                unique_urls.append(url)
        
        return unique_urls

    def get_oembed_provider(self, url):
        """Findet den passenden oEmbed Provider für eine URL"""
        domain = urlparse(url).netloc.lower()
        
        # Entferne www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Suche nach exakter Domain oder Subdomain
        for provider_domain, endpoint in self.oembed_providers.items():
            if domain == provider_domain or domain.endswith('.' + provider_domain):
                return endpoint
        
        return None

    def fetch_oembed_preview(self, url):
        """Holt oEmbed Preview für eine URL"""
        try:
            oembed_endpoint = self.get_oembed_provider(url)
            if not oembed_endpoint:
                return None
            
            # oEmbed Request
            params = {
                'url': url,
                'format': 'json',
                'maxwidth': 400,
                'maxheight': 300
            }
            
            response = self.session.get(
                oembed_endpoint, 
                params=params, 
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                return {
                    'url': url,
                    'title': data.get('title', ''),
                    'description': data.get('description', ''),
                    'image': data.get('thumbnail_url', ''),
                    'site_name': data.get('provider_name', ''),
                    'favicon': None,
                    'type': 'oembed',
                    'html': data.get('html', ''),  # Für Videos/Embeds
                    'width': data.get('width'),
                    'height': data.get('height')
                }
                
        except Exception as e:
            logger.debug(f"oEmbed failed for {url}: {e}")
            return None

    def fetch_quick_meta(self, url):
        """Schneller Meta-Tag fetch (nur Header und erste 8KB)"""
        try:
            # Nur erste 8KB laden für Meta-Tags
            response = self.session.get(
                url, 
                timeout=self.timeout,
                stream=True,
                headers={'Range': 'bytes=0-8191'}  # Nur erste 8KB
            )
            
            if response.status_code not in [200, 206]:
                return None
            
            # Lese nur genug für <head> section
            content = b''
            for chunk in response.iter_content(chunk_size=1024):
                content += chunk
                if len(content) >= 8192 or b'</head>' in content:
                    break
            
            content_str = content.decode('utf-8', errors='ignore')
            
            # Quick regex für Meta-Tags (schneller als BeautifulSoup)
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', content_str, re.IGNORECASE)
            og_title_match = re.search(r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']', content_str, re.IGNORECASE)
            og_desc_match = re.search(r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\']([^"\']+)["\']', content_str, re.IGNORECASE)
            og_image_match = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', content_str, re.IGNORECASE)
            
            title = og_title_match.group(1) if og_title_match else (title_match.group(1) if title_match else '')
            description = og_desc_match.group(1) if og_desc_match else ''
            image = og_image_match.group(1) if og_image_match else ''
            
            if title or description:
                return {
                    'url': url,
                    'title': title[:100],  # Limit
                    'description': description[:200],  # Limit
                    'image': image,
                    'site_name': urlparse(url).netloc,
                    'favicon': f"https://www.google.com/s2/favicons?domain={urlparse(url).netloc}",
                    'type': 'meta'
                }
                
        except Exception as e:
            logger.debug(f"Quick meta failed for {url}: {e}")
            return None

    def generate_fast_previews(self, content):
        """Generiert schnelle Previews mit Fallback-Strategie"""
        if not content:
            return []
        
        urls = self.extract_urls_from_text(content)
        previews = []
        
        for url in urls[:3]:  # Max 3 URLs
            preview = None
            
            # 1. Versuche oEmbed (schnellste Option)
            preview = self.fetch_oembed_preview(url)
            
            # 2. Fallback: Schneller Meta-Tag fetch
            if not preview:
                preview = self.fetch_quick_meta(url)
            
            if preview:
                previews.append(preview)
        
        return previews


# Global instance
fast_preview_generator = OEmbedPreviewGenerator()

def get_fast_link_previews(content):
    """Schnelle Helper-Funktion für Templates"""
    return fast_preview_generator.generate_fast_previews(content)
