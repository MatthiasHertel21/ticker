"""
Telethon-basierter Telegram Scraper
Nutzt User-Account statt Bot für vollständigen Kanalzugriff
"""

from telethon import TelegramClient, events
from telethon.tl.types import Channel, Chat, User
import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import re
import html
from app.data import json_manager
import os

logger = logging.getLogger(__name__)

# Globaler Event Loop für Telethon
_global_loop = None

def get_or_create_event_loop():
    """Gibt den globalen Event Loop zurück oder erstellt einen neuen"""
    global _global_loop
    
    try:
        # Versuche den aktuellen Event Loop zu bekommen
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Event loop is closed")
        return loop
    except RuntimeError:
        # Erstelle einen neuen Event Loop wenn keiner existiert
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            _global_loop = loop
            logger.info("Neuer Event Loop für Telethon erstellt")
            return loop
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Event Loops: {e}")
            # Fallback: Erstelle minimal Event Loop
            import threading
            if threading.current_thread() == threading.main_thread():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                return loop
            else:
                # In Worker Thread: Nutze run_until_complete Wrapper
                return None


class TelethonChannelScraper:
    """Telegram Channel Scraper mit Telethon User Client - Web-kompatibel"""
    
    def __init__(self):
        self.client = None
        self.session_name = '/app/data/telethon_session'
        self._temp_client = None
        self._phone_code_hash = None
        
    def start_auth(self, api_id, api_hash, phone):
        """Startet den Authentifizierungsprozess (sendet SMS) - synchron"""
        try:
            logger.info(f"Starte Telethon Authentifizierung für {phone}")
            
            # Verwende den globalen Event Loop
            loop = get_or_create_event_loop()
            
            self._temp_client = TelegramClient(
                self.session_name,
                int(api_id),
                api_hash,
                loop=loop
            )
            
            # Verbinde synchron mit run_until_complete
            loop.run_until_complete(self._temp_client.connect())
            
            # Prüfe ob bereits authentifiziert
            if loop.run_until_complete(self._temp_client.is_user_authorized()):
                self.client = self._temp_client
                logger.info("Benutzer ist bereits authentifiziert")
                return {'success': True, 'already_authorized': True}
            
            # Sende Authentifizierungs-Code
            result = loop.run_until_complete(self._temp_client.send_code_request(phone))
            phone_code_hash = result.phone_code_hash
            
            # Speichere den Hash für später
            self._phone_code_hash = phone_code_hash
            
            logger.info("SMS-Code wurde gesendet")
            return {
                'success': True, 
                'code_sent': True,
                'phone_code_hash': phone_code_hash
            }
            
        except Exception as e:
            logger.error(f"Fehler beim Starten der Authentifizierung: {e}")
            if self._temp_client:
                try:
                    loop.run_until_complete(self._temp_client.disconnect())
                except:
                    pass
            return {'success': False, 'error': str(e)}
    
    def complete_auth(self, phone, code, password=None):
        """Vervollständigt die Authentifizierung mit dem SMS-Code - synchron"""
        try:
            if not self._temp_client or not self._phone_code_hash:
                return {'success': False, 'error': 'Authentifizierung wurde nicht gestartet'}
            
            logger.info("Vervollständige Authentifizierung mit SMS-Code")
            
            # Verwende den gleichen Event Loop
            loop = get_or_create_event_loop()
            
            try:
                # Authentifiziere mit dem Code
                loop.run_until_complete(self._temp_client.sign_in(
                    phone=phone,
                    code=code,
                    phone_code_hash=self._phone_code_hash
                ))
                
            except Exception as signin_error:
                error_msg = str(signin_error)
                if "Two-steps verification" in error_msg or "password is required" in error_msg:
                    logger.info("2FA erkannt - Passwort erforderlich")
                    if not password:
                        return {
                            'success': False, 
                            'error': 'two_factor_required',
                            'message': 'Zwei-Faktor-Authentifizierung ist aktiviert. Bitte gib dein Telegram-Passwort ein.'
                        }
                    
                    # Authentifiziere mit 2FA-Passwort
                    try:
                        loop.run_until_complete(self._temp_client.sign_in(password=password))
                        logger.info("2FA-Authentifizierung erfolgreich")
                    except Exception as pwd_error:
                        logger.error(f"2FA-Passwort fehlgeschlagen: {pwd_error}")
                        return {'success': False, 'error': f'Falsches Passwort: {pwd_error}'}
                else:
                    # Anderer Fehler
                    raise signin_error
            
            # Prüfe ob erfolgreich
            if loop.run_until_complete(self._temp_client.is_user_authorized()):
                self.client = self._temp_client
                me = loop.run_until_complete(self._temp_client.get_me())
                logger.info(f"Telethon Authentifizierung erfolgreich: {me.first_name}")
                return {'success': True, 'authenticated': True, 'user': me.first_name}
            else:
                return {'success': False, 'error': 'Authentifizierung fehlgeschlagen'}
            
        except Exception as e:
            logger.error(f"Fehler bei der Code-Verifizierung: {e}")
            if self._temp_client:
                try:
                    loop = get_or_create_event_loop()
                    loop.run_until_complete(self._temp_client.disconnect())
                except:
                    pass
            return {'success': False, 'error': str(e)}

    def is_ready(self):
        """Prüft ob der Client bereit ist"""
        try:
            # Wenn kein Client existiert, versuche ihn zu laden
            if not self.client:
                self._load_existing_session()
            
            if not self.client:
                return False
            
            # Verwende den gleichen Event Loop
            loop = get_or_create_event_loop()
            
            # Prüfe Authentifizierung mit detailliertem Logging
            is_authorized = loop.run_until_complete(self.client.is_user_authorized())
            logger.info(f"Telethon Authentifizierung Status: {is_authorized}")
            
            if not is_authorized:
                logger.warning("Client ist verbunden aber nicht authentifiziert - Session möglicherweise abgelaufen")
                # Versuche ein einfaches Get-Request um zu testen
                try:
                    me = loop.run_until_complete(self.client.get_me())
                    if me:
                        logger.info(f"User gefunden trotz is_user_authorized=False: {me.first_name}")
                        return True
                except Exception as e:
                    logger.error(f"get_me() fehlgeschlagen: {e}")
                    return False
            
            return is_authorized
            
        except Exception as e:
            logger.error(f"Fehler beim Prüfen der Authentifizierung: {e}")
            return False

    def _load_existing_session(self):
        """Lädt eine existierende Session, falls vorhanden"""
        try:
            import os
            session_file = f"{self.session_name}.session"
            
            if not os.path.exists(session_file):
                logger.info("Keine existierende Telethon-Session gefunden")
                return False
            
            # API-Konfiguration laden
            api_id = os.getenv('TELEGRAM_API_ID')
            api_hash = os.getenv('TELEGRAM_API_HASH')
            
            if not all([api_id, api_hash]):
                logger.error("TELEGRAM_API_ID oder TELEGRAM_API_HASH nicht gesetzt")
                return False
            
            logger.info(f"Lade existierende Telethon-Session: {session_file}")
            
            # Client mit existierender Session erstellen - OHNE Event Loop
            self.client = TelegramClient(self.session_name, int(api_id), api_hash)
            
            logger.info("Telethon-Session erfolgreich geladen")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Session: {e}")
            self.client = None
            return False

    def scrape_channels(self, limit=10):
        """Synchrone Wrapper-Methode für Background-Tasks"""
        try:
            logger.info("Starte synchrones Telethon-Scraping")
            
            # Prüfe Session
            if not self.client:
                if not self._load_existing_session():
                    logger.error("Keine gültige Telethon-Session verfügbar")
                    return 0
            
            # Event Loop Handling für Celery Worker
            try:
                # Verwende asyncio.run für bessere Isolation
                new_articles = asyncio.run(self._scrape_channels(limit))
            except RuntimeError as e:
                if "This event loop is already running" in str(e):
                    # Fallback für bereits laufende Event Loops
                    logger.warning("Event Loop bereits aktiv, verwende Thread-Pool")
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self._scrape_channels(limit))
                        new_articles = future.result(timeout=300)
                else:
                    raise e
            
            logger.info(f"Synchrones Telethon-Scraping abgeschlossen: {new_articles} neue Artikel")
            return new_articles
            
        except Exception as e:
            logger.error(f"Fehler beim synchronen Telethon-Scraping: {e}")
            return 0

    async def _scrape_channels(self, limit=10):
        """Interne Async-Methode zum Scrapen der Kanäle"""
        try:
            if not self.client:
                return 0
            
            # Client starten, wenn nicht bereits gestartet
            if not self.client.is_connected():
                await self.client.start()
            
            # Lade konfigurierte Kanäle aus sources.json
            sources = json_manager.read('sources')
            configured_channels = []
            
            for source_id, source_data in sources.get('sources', {}).items():
                if (source_data.get('type') == 'telegram' and 
                    source_data.get('is_active', True) and 
                    source_data.get('channel_username')):
                    configured_channels.append(source_data['channel_username'])
            
            if not configured_channels:
                logger.warning("Keine aktiven Telegram-Kanäle in sources.json gefunden")
                return 0
            
            logger.info(f"Scrape {len(configured_channels)} konfigurierte Kanäle: {configured_channels}")
            
            new_articles = 0
            
            for channel in configured_channels:
                try:
                    logger.info(f"Scrape Kanal: {channel}")
                    
                    # Hole mehr Nachrichten für bessere Abdeckung der letzten Stunde (20 pro Kanal)
                    messages = await self.client.get_messages(channel, limit=min(20, 50))
                    
                    # Filtere nach Nachrichten der letzten Stunde (mit Duplikatsschutz)
                    one_hour_ago = datetime.now() - timedelta(hours=1)
                    
                    for message in messages:
                        if message.text and len(message.text.strip()) > 50:  # Nur längere Nachrichten
                            # Prüfe Alter der Nachricht
                            message_age = "recent"
                            if message.date:
                                if message.date.replace(tzinfo=None) >= one_hour_ago:
                                    message_age = "last_hour"
                                elif message.date.replace(tzinfo=None) >= datetime.now() - timedelta(hours=6):
                                    message_age = "last_6_hours"
                                else:
                                    message_age = "older"
                            
                            # Bevorzuge Nachrichten der letzten Stunde, aber nimm auch andere
                            # (der Duplikatsschutz verhindert mehrfache Speicherung)
                            
                            # Extrahiere Bilder und Medien
                            media_info = await self._extract_media_info(message)
                            
                            # Generiere Link-Previews asynchron für URLs im Text
                            link_previews = await self._generate_link_previews_async(message.text)
                            
                            # Erstelle Artikel-Objekt
                            article = {
                                'id': f"telegram_{channel}_{message.id}",
                                'title': self._extract_title(message.text),
                                'content': self._extract_content(message.text),
                                'full_text': message.text,  # Vollständiger Text für Detailansicht
                                'source': f"Telegram - {channel}",
                                'channel': channel,
                                'url': f"https://t.me/{channel}/{message.id}",
                                'published_date': message.date.isoformat() if message.date else datetime.now().isoformat(),
                                'scraped_date': datetime.now().isoformat(),
                                'platform': 'telegram',
                                'message_age': message_age,
                                'media': media_info,  # Bilder und Medien-Informationen
                                'link_previews': link_previews  # Vorgenerierte Link-Previews
                            }
                            
                            # Speichere Artikel (Duplikatsschutz aktiv)
                            if self._save_article(article):
                                new_articles += 1
                                age_info = "🕐" if message_age == "last_hour" else "🕕" if message_age == "last_6_hours" else "📰"
                                logger.info(f"{age_info} Artikel gespeichert: {article['title'][:50]}...")
                            
                except Exception as e:
                    logger.warning(f"Fehler beim Scrapen von Kanal {channel}: {e}")
                    continue
            
            logger.info(f"Telethon-Scraping abgeschlossen: {new_articles} Nachrichten gefunden")
            
            # Zusätzliche Statistik über Artikel-Alter
            if new_articles > 0:
                recent_stats = self._get_recent_articles_stats()
                logger.info(f"📊 Artikel-Verteilung: {recent_stats}")
            
            return new_articles
            
        except Exception as e:
            logger.error(f"Fehler beim Scraping: {e}")
            return 0

    def _extract_title(self, text):
        """Extrahiert einen Titel aus dem Nachrichtentext"""
        try:
            # Nimm die erste Zeile als Titel
            lines = text.strip().split('\n')
            title = lines[0].strip()
            
            # Entferne Telegram-Markup aus dem Titel
            title = self._clean_markup(title)
            
            # Begrenze Titel-Länge
            if len(title) > 100:
                title = title[:97] + "..."
            
            # Falls der Titel zu kurz ist, nimm mehr Text
            if len(title) < 20 and len(lines) > 1:
                second_line = self._clean_markup(lines[1].strip())
                title = (title + " " + second_line).strip()[:100]
            
            return title if title else "Telegram Nachricht"
            
        except Exception:
            return "Telegram Nachricht"

    def _clean_markup(self, text):
        """Entfernt Telegram-Markup aus Text"""
        if not text:
            return text
        
        # Entferne ** und __ (fett)
        text = text.replace('**', '').replace('__', '')
        
        # Entferne * und _ (kursiv) - aber vorsichtig
        import re
        text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'\1', text)
        text = re.sub(r'(?<!_)_([^_]+?)_(?!_)', r'\1', text)
        
        # Entferne ` (code)
        text = text.replace('`', '')
        
        return text.strip()

    def _extract_content(self, text):
        """Extrahiert den Content ohne die Titel-Zeile"""
        try:
            lines = text.strip().split('\n')
            
            # Wenn nur eine Zeile vorhanden ist, return leer
            if len(lines) <= 1:
                return ""
            
            # Überspringe die erste Zeile (Titel) und nimm den Rest
            content_lines = lines[1:]
            
            # Entferne leere Zeilen am Anfang
            while content_lines and not content_lines[0].strip():
                content_lines.pop(0)
            
            # Entferne "Zum Artikel" Links
            filtered_lines = []
            for line in content_lines:
                line = line.strip()
                # Überspringe "[Zum Artikel]" und ähnliche Links
                if line.startswith('[') and 'artikel' in line.lower():
                    continue
                if line.startswith('http') and line == lines[-1].strip():
                    # Behalte URL, aber nur wenn es eine echte URL ist, nicht nur ein Link-Text
                    pass
                filtered_lines.append(line)
            
            return '\n'.join(filtered_lines).strip()
            
        except Exception:
            return text

    def _save_article(self, article):
        """Speichert einen Artikel in der JSON-Datenbank"""
        try:
            # Verwende den json_manager mit der korrekten API
            articles_data = json_manager.read('articles')  # Ohne .json Extension
            
            # Wenn articles_data leer ist oder kein articles-Key existiert
            if not articles_data or 'articles' not in articles_data:
                articles_data = {'articles': []}
            
            articles = articles_data['articles']
            
            # Stelle sicher, dass articles eine Liste ist
            if not isinstance(articles, list):
                articles = []
                articles_data['articles'] = articles
            
            # Prüfe auf Duplikate (nach ID, Titel oder URL)
            for existing in articles:
                # Prüfe ID
                if existing.get('id') == article['id']:
                    return False
                
                # Prüfe Titel + Channel (ähnliche Artikel)
                if (existing.get('title') == article['title'] and 
                    existing.get('channel') == article['channel']):
                    return False
                
                # Prüfe URL
                if existing.get('url') == article['url']:
                    return False
            
            # Füge neuen Artikel hinzu
            articles.append(article)
            articles_data['articles'] = articles
            
            # Speichere zurück
            json_manager.write('articles', articles_data)  # Ohne .json Extension
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Artikels: {e}")
            return False

    def _get_recent_articles_stats(self):
        """Gibt Statistiken über kürzlich gescrapte Artikel zurück"""
        try:
            articles_data = json_manager.read('articles')
            articles = articles_data.get('articles', [])
            
            # Zähle nach Alter
            now = datetime.now()
            one_hour_ago = now - timedelta(hours=1)
            six_hours_ago = now - timedelta(hours=6)
            
            last_hour = 0
            last_6_hours = 0
            older = 0
            
            for article in articles:
                if article.get('platform') == 'telegram':
                    pub_date_str = article.get('published_date', '')
                    try:
                        # Parse ISO datetime
                        pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                        pub_date = pub_date.replace(tzinfo=None)  # Remove timezone for comparison
                        
                        if pub_date >= one_hour_ago:
                            last_hour += 1
                        elif pub_date >= six_hours_ago:
                            last_6_hours += 1
                        else:
                            older += 1
                    except:
                        older += 1
            
            return f"🕐 Letzte Stunde: {last_hour}, 🕕 Letzte 6h: {last_6_hours}, 📰 Älter: {older}"
            
        except Exception as e:
            logger.error(f"Fehler bei Statistik-Erstellung: {e}")
            return "Statistik nicht verfügbar"

    async def _generate_link_previews_async(self, text):
        """Generiert Link-Previews asynchron während des Scrapings"""
        try:
            from app.utils.oembed_preview import OEmbedPreviewGenerator
            import asyncio
            import aiohttp
            
            if not text:
                return []
            
            # Extrahiere URLs aus dem Text
            import re
            url_pattern = r'https?://[^\s<>"]+[^\s<>".,;!?]'
            urls = re.findall(url_pattern, text, re.IGNORECASE)
            
            if not urls:
                return []
            
            # Bereinige URLs
            unique_urls = []
            for url in urls:
                url = url.rstrip('.,;!?)')
                if url not in unique_urls:
                    unique_urls.append(url)
            
            # Maximal 3 URLs für Performance
            unique_urls = unique_urls[:3]
            
            previews = []
            preview_gen = OEmbedPreviewGenerator()
            
            # Generiere Previews parallel für bessere Performance
            tasks = []
            for url in unique_urls:
                task = self._fetch_single_preview_async(preview_gen, url)
                tasks.append(task)
            
            # Führe alle Preview-Requests parallel aus mit Timeout
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True), 
                    timeout=15  # Max 15 Sekunden für alle Previews
                )
                
                for result in results:
                    if isinstance(result, dict) and result:
                        previews.append(result)
                        
            except asyncio.TimeoutError:
                logger.warning(f"Link-Preview Timeout für URLs: {unique_urls}")
                
            logger.debug(f"Generierte {len(previews)} Previews für {len(unique_urls)} URLs")
            return previews
            
        except Exception as e:
            logger.warning(f"Fehler bei Link-Preview-Generierung: {e}")
            return []

    async def _fetch_single_preview_async(self, preview_gen, url):
        """Holt eine einzelne Preview asynchron"""
        try:
            # Nutze den synchronen Code, aber mit Timeout
            import asyncio
            import functools
            
            # Führe die synchrone Preview-Generierung in einem Thread-Pool aus
            loop = asyncio.get_event_loop()
            
            # oEmbed versuchen
            preview = await loop.run_in_executor(
                None, 
                functools.partial(preview_gen.fetch_oembed_preview, url)
            )
            
            # Fallback zu Quick Meta
            if not preview:
                preview = await loop.run_in_executor(
                    None,
                    functools.partial(preview_gen.fetch_quick_meta, url)
                )
            
            return preview
            
        except Exception as e:
            logger.debug(f"Preview-Fetch fehlgeschlagen für {url}: {e}")
            return None

    async def _extract_media_info(self, message):
        """Extrahiert Medien-Informationen aus einer Telegram-Nachricht"""
        media_info = {
            'has_media': False,
            'media_type': None,
            'images': [],
            'videos': [],
            'documents': []
        }
        
        try:
            if message.media:
                media_info['has_media'] = True
                
                # Foto
                if hasattr(message.media, 'photo') and message.media.photo:
                    media_info['media_type'] = 'photo'
                    
                    # Lade das Bild herunter und speichere es lokal
                    try:
                        photo_id = str(message.media.photo.id)
                        photo_filename = f"telegram_photo_{photo_id}.jpg"
                        photo_path = f"/app/data/media/{photo_filename}"
                        
                        # Stelle sicher, dass der Media-Ordner existiert
                        import os
                        os.makedirs("/app/data/media", exist_ok=True)
                        
                        # Download des Bildes
                        await self.client.download_media(message.media, photo_path)
                        
                        # Telegram-interne Bild-ID (für API-Zugriff)
                        media_info['images'].append({
                            'id': photo_id,
                            'type': 'telegram_photo',
                            'filename': photo_filename,
                            'local_path': photo_path,
                            'access_hash': str(message.media.photo.access_hash) if hasattr(message.media.photo, 'access_hash') else None
                        })
                        logger.info(f"Bild gespeichert: {photo_filename}")
                    except Exception as e:
                        logger.warning(f"Fehler beim Speichern des Bildes: {e}")
                        # Fallback ohne lokale Speicherung
                        media_info['images'].append({
                            'id': str(message.media.photo.id),
                            'type': 'telegram_photo',
                            'access_hash': str(message.media.photo.access_hash) if hasattr(message.media.photo, 'access_hash') else None
                        })
                
                # Video
                elif hasattr(message.media, 'document') and message.media.document:
                    doc = message.media.document
                    if doc.mime_type and doc.mime_type.startswith('video/'):
                        media_info['media_type'] = 'video'
                        media_info['videos'].append({
                            'id': str(doc.id),
                            'mime_type': doc.mime_type,
                            'size': doc.size,
                            'type': 'telegram_video'
                        })
                    else:
                        media_info['media_type'] = 'document'
                        media_info['documents'].append({
                            'id': str(doc.id),
                            'mime_type': doc.mime_type,
                            'size': doc.size,
                            'file_name': getattr(doc, 'file_name', 'unknown'),
                            'type': 'telegram_document'
                        })
                
                # Web Preview mit Bildern
                elif hasattr(message.media, 'webpage') and message.media.webpage:
                    webpage = message.media.webpage
                    if hasattr(webpage, 'photo') and webpage.photo:
                        media_info['media_type'] = 'web_preview'
                        media_info['images'].append({
                            'type': 'web_preview',
                            'url': webpage.url if hasattr(webpage, 'url') else None,
                            'title': webpage.title if hasattr(webpage, 'title') else None,
                            'description': webpage.description if hasattr(webpage, 'description') else None
                        })
        
        except Exception as e:
            logger.debug(f"Fehler bei Medien-Extraktion: {e}")
        
        return media_info

    async def _download_media(self, media_id):
        """Lädt ein Telegram-Medium herunter"""
        try:
            if not self.client:
                logger.error("Kein Telegram Client verfügbar")
                return None
            
            # Suche in den letzten Nachrichten nach der Media-ID
            from app.data import json_manager
            articles = json_manager.read('articles')
            
            for article in articles.get('articles', []):
                if article.get('media') and article['media'].get('images'):
                    for img in article['media']['images']:
                        if img.get('id') == media_id and img.get('type') == 'telegram_photo':
                            # Lade das Bild von Telegram herunter
                            from telethon.tl.types import InputPhotoFileLocation
                            from telethon.tl.types import InputPeerEmpty
                            
                            # Versuche das Bild herunterzuladen
                            import io
                            buffer = io.BytesIO()
                            
                            # Verwende die photo ID für den Download
                            try:
                                photo_id = int(img['id'])
                                access_hash = int(img.get('access_hash', 0))
                                
                                # Download der Datei
                                file_location = InputPhotoFileLocation(
                                    id=photo_id,
                                    access_hash=access_hash,
                                    file_reference=b'',
                                    thumb_size='m'
                                )
                                
                                await self.client.download_file(file_location, buffer)
                                return buffer.getvalue()
                                
                            except Exception as e:
                                logger.debug(f"Direkter Download fehlgeschlagen: {e}")
                                # Fallback: Versuche über Nachricht
                                return None
            
            logger.warning(f"Media ID {media_id} nicht gefunden")
            return None
            
        except Exception as e:
            logger.error(f"Fehler beim Media-Download: {e}")
            return None

    def initialize(self, api_id, api_hash, phone):
        """Legacy-Methode für Kompatibilität - prüft vorhandene Session"""
        try:
            # Verwende den globalen Event Loop
            loop = get_or_create_event_loop()
            
            # Erstelle Client für Prüfung
            test_client = TelegramClient(
                self.session_name,
                int(api_id),
                api_hash,
                loop=loop
            )
            
            loop.run_until_complete(test_client.connect())
            
            if loop.run_until_complete(test_client.is_user_authorized()):
                self.client = test_client
                logger.info("Telethon Client bereits authentifiziert")
                return True
            else:
                # Nicht authentifiziert, trenne Verbindung
                loop.run_until_complete(test_client.disconnect())
                return False
            
        except Exception as e:
            logger.error(f"Fehler beim Initialisieren des Telethon Clients: {e}")
            return False


# Globale Scraper-Instanz für persistenten State
_global_scraper = None

def get_global_scraper():
    """Gibt die globale Scraper-Instanz zurück"""
    global _global_scraper
    if _global_scraper is None:
        _global_scraper = TelethonChannelScraper()
    return _global_scraper

# Synchrone Wrapper-Funktionen
def sync_start_telethon_auth(api_id, api_hash, phone):
    """Synchroner Wrapper für Authentifizierung starten"""
    scraper = get_global_scraper()
    return scraper.start_auth(api_id, api_hash, phone)

def sync_complete_telethon_auth(phone, code, password=None):
    """Synchroner Wrapper für Authentifizierung abschließen"""
    scraper = get_global_scraper()
    return scraper.complete_auth(phone, code, password)

def sync_check_telethon_ready():
    """Prüft ob Telethon bereit ist"""
    scraper = get_global_scraper()
    return scraper.is_ready()

def sync_scrape_telegram_telethon(limit=10):
    """Synchroner Wrapper für Telethon-Scraping"""
    scraper = get_global_scraper()
    
    # Prüfe ob authentifiziert
    if not scraper.is_ready():
        logger.error("Telethon Client nicht authentifiziert")
        return 0
    
    try:
        # Hole Event Loop
        loop = get_or_create_event_loop()
        
        # Führe Scraping aus
        result = loop.run_until_complete(scraper._scrape_channels(limit))
        return result
        
    except Exception as e:
        logger.error(f"Fehler beim Telethon-Scraping: {e}")
        return 0


def download_telegram_media(media_id):
    """Synchroner Wrapper für Media-Download"""
    scraper = get_global_scraper()
    
    if not scraper.is_ready():
        logger.error("Telethon Client nicht authentifiziert")
        return None
    
    try:
        loop = get_or_create_event_loop()
        result = loop.run_until_complete(scraper._download_media(media_id))
        return result
    except Exception as e:
        logger.error(f"Fehler beim Media-Download: {e}")
        return None
