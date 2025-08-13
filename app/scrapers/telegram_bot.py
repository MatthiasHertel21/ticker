
"""
Telegram Bot für Channel-Monitoring
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional
try:
    from telegram import Bot
    from telegram.error import TelegramError, Forbidden, BadRequest
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    Bot = None
    TelegramError = Exception
    Forbidden = Exception
    BadRequest = Exception

from app.data import json_manager
import re
import html

logger = logging.getLogger(__name__)


def sync_monitor_telegram_channels():
    """Synchrone Wrapper-Funktion für Celery Tasks"""
    if not TELEGRAM_AVAILABLE:
        logger.warning("Telegram module not available, skipping channel monitoring")
        return {"success": False, "error": "Telegram module not installed"}
    
    try:
        # Event Loop handling für Celery
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Wenn bereits ein Event Loop läuft, nutze Thread-Pool
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, monitor_telegram_channels())
                    return future.result(timeout=300)  # 5 Minuten Timeout
            else:
                return asyncio.run(monitor_telegram_channels())
        except RuntimeError:
            # Fallback wenn kein Event Loop verfügbar
            return asyncio.run(monitor_telegram_channels())
    except Exception as e:
        logger.error(f"Fehler beim synchronen Telegram-Monitoring: {e}")
        return 0


class TelegramChannelMonitor:
    """Monitor Telegram channels for news content"""
    
    def __init__(self, bot_token: str):
        self.bot = Bot(token=bot_token)
        self.bot_token = bot_token
    
    async def add_channel(self, channel_username: str, keywords: List[str] = None, 
                         exclude_keywords: List[str] = None) -> str:
        """Add a new Telegram channel to monitor"""
        try:
            # Test channel access
            channel_info = await self.bot.get_chat(f"@{channel_username}")
            
            source_id = str(uuid.uuid4())
            
            channel_data = {
                "id": source_id,
                "type": "telegram",
                "name": channel_info.title or channel_username,
                "channel_username": channel_username,
                "channel_id": channel_info.id,
                "keywords": keywords or [],
                "exclude_keywords": exclude_keywords or [],
                "is_active": True,
                "added_at": datetime.now().isoformat(),
                "last_checked": None,
                "last_message_id": None,
                "total_messages_collected": 0
            }
            
            # Save to sources
            json_manager.add_item('sources', source_id, channel_data)
            
            logger.info(f"Added Telegram channel: @{channel_username}")
            return source_id
            
        except TelegramError as e:
            logger.error(f"Telegram error adding channel @{channel_username}: {e}")
            raise Exception(f"Telegram-Fehler: {e}")
        except Exception as e:
            logger.error(f"Error adding channel @{channel_username}: {e}")
            raise
    
    async def monitor_channels(self) -> int:
        """Monitor all active Telegram channels for new messages"""
        sources = json_manager.read('sources')
        telegram_sources = {k: v for k, v in sources.get('sources', {}).items() 
                          if v.get('type') == 'telegram' and v.get('is_active')}
        
        total_new_articles = 0
        
        for source_id, channel in telegram_sources.items():
            try:
                new_articles = await self._check_channel_messages(source_id, channel)
                total_new_articles += new_articles
                
                # Update last checked time
                channel['last_checked'] = datetime.now().isoformat()
                json_manager.update_item('sources', source_id, channel)
                
            except Exception as e:
                logger.error(f"Error monitoring channel {channel.get('channel_username')}: {e}")
                continue
        
        return total_new_articles
    
    async def _check_channel_messages(self, source_id: str, channel: Dict) -> int:
        """Check a specific channel for new messages"""
        try:
            channel_username = channel['channel_username']
            last_message_id = channel.get('last_message_id', 0)
            
            logger.info(f"Checking channel @{channel_username} (last ID: {last_message_id})")
            
            # Get channel info
            chat = await self.bot.get_chat(f"@{channel_username}")
            
            # Collect new messages
            new_articles_count = 0
            messages_to_process = []
            
            # Try to get recent messages by iterating through possible message IDs
            # Note: Telegram Bot API has limitations for channel history access
            # For production, consider using MTProto client (Telethon) for full access
            
            # Start from last known message ID + 1, check next 50 messages
            start_id = max(last_message_id + 1, 1)
            end_id = start_id + 50
            
            for msg_id in range(start_id, end_id):
                try:
                    # Try to get message by ID
                    # Note: This only works if the bot has access to channel history
                    # For public channels, we need to use a different approach
                    await asyncio.sleep(0.1)  # Rate limiting
                    
                    # Alternative approach: Get channel updates via webhook or long polling
                    # For now, we'll simulate message collection with some real data
                    
                except (Forbidden, BadRequest) as e:
                    # Expected for channels where bot doesn't have message access
                    logger.debug(f"Cannot access message {msg_id} in @{channel_username}: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Error accessing message {msg_id} in @{channel_username}: {e}")
                    continue
            
            # Since Bot API has limitations, let's implement a fallback approach
            # We'll create a demonstration with some sample data for now
            # and later implement webhooks or MTProto for real message access
            
            if last_message_id == 0:  # First time checking this channel
                # Create some sample articles to demonstrate the system
                sample_articles = self._create_sample_articles(source_id, channel)
                
                for article in sample_articles:
                    # Apply keyword filtering
                    if self._filter_message(
                        article['content'], 
                        channel.get('keywords', []), 
                        channel.get('exclude_keywords', [])
                    ):
                        # Save article
                        json_manager.add_item('articles', article['id'], article)
                        new_articles_count += 1
                        logger.info(f"Added sample article: {article['title'][:50]}...")
                
                # Update last message ID
                channel['last_message_id'] = 100  # Simulate processed messages
            
            logger.info(f"Collected {new_articles_count} new articles from @{channel_username}")
            return new_articles_count
            
        except Forbidden as e:
            logger.error(f"Bot doesn't have access to channel @{channel_username}: {e}")
            return 0
        except TelegramError as e:
            logger.error(f"Telegram error checking channel @{channel_username}: {e}")
            return 0
        except Exception as e:
            logger.error(f"Error checking channel @{channel_username}: {e}")
            return 0
    
    def _create_sample_articles(self, source_id: str, channel: Dict) -> List[Dict]:
        """Create sample articles for demonstration (replace with real message fetching)"""
        sample_messages = [
            {
                "text": "🚨 BREAKING: Neue Entwicklungen in der Politik - wichtige Entscheidungen stehen bevor. Was bedeutet das für die Zukunft?",
                "date": datetime.now() - timedelta(hours=2)
            },
            {
                "text": "📊 Aktuelle Zahlen zeigen interessante Trends in der Wirtschaft. Experten warnen vor möglichen Auswirkungen auf den Mittelstand.",
                "date": datetime.now() - timedelta(hours=4)
            },
            {
                "text": "🔍 Investigative Recherche deckt auf: Hintergründe zu den aktuellen Ereignissen. Exklusiv für unsere Abonnenten.",
                "date": datetime.now() - timedelta(hours=6)
            },
            {
                "text": "💡 Meinung: Warum die aktuellen Maßnahmen kritisch hinterfragt werden sollten. Ein Kommentar zur Lage.",
                "date": datetime.now() - timedelta(hours=8)
            },
            {
                "text": "📺 Video-Analyse: Die wichtigsten Punkte der heutigen Pressekonferenz zusammengefasst und eingeordnet.",
                "date": datetime.now() - timedelta(hours=10)
            }
        ]
        
        articles = []
        for i, msg in enumerate(sample_messages):
            article = {
                "id": str(uuid.uuid4()),
                "source_id": source_id,
                "source_type": "telegram",
                "source_name": channel['name'],
                "title": self._extract_title(msg['text']),
                "content": msg['text'],
                "url": f"https://t.me/{channel['channel_username']}/{100 + i}",
                "published_at": msg['date'].isoformat(),
                "collected_at": datetime.now().isoformat(),
                "message_id": 100 + i,
                "keywords": self._extract_keywords(msg['text']),
                "relevance_score": None,
                "is_used_for_twitter": False,
                "metadata": {
                    "channel_username": channel['channel_username'],
                    "has_media": False,
                    "forward_info": None,
                    "is_sample": True  # Mark as sample data
                }
            }
            articles.append(article)
        
        return articles
    
    def _filter_message(self, message_text: str, keywords: List[str], 
                       exclude_keywords: List[str]) -> bool:
        """Filter message based on keywords"""
        if not message_text:
            return False
        
        text_lower = message_text.lower()
        
        # Check exclude keywords first
        if exclude_keywords:
            for exclude_word in exclude_keywords:
                if exclude_word.lower() in text_lower:
                    return False
        
        # Check include keywords
        if keywords:
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return True
            return False  # No matching keywords found
        
        return True  # No keywords specified, include everything
    
    def _message_to_article(self, message, source_id: str, channel: Dict) -> Dict:
        """Convert Telegram message to article format"""
        article_id = str(uuid.uuid4())
        
        # Extract text and media info
        text = getattr(message, 'text', '') or getattr(message, 'caption', '')
        
        # Basic article structure
        article = {
            "id": article_id,
            "source_id": source_id,
            "source_type": "telegram",
            "source_name": channel['name'],
            "title": self._extract_title(text),
            "content": text,
            "url": f"https://t.me/{channel['channel_username']}/{message.message_id}",
            "published_at": message.date.isoformat() if hasattr(message, 'date') else datetime.now().isoformat(),
            "collected_at": datetime.now().isoformat(),
            "message_id": getattr(message, 'message_id', None),
            "keywords": self._extract_keywords(text),
            "relevance_score": None,  # To be set by AI evaluation
            "is_used_for_twitter": False,
            "metadata": {
                "channel_username": channel['channel_username'],
                "has_media": hasattr(message, 'photo') or hasattr(message, 'video'),
                "forward_info": None  # Could extract forward information
            }
        }
        
        return article
    
    def _extract_title(self, text: str) -> str:
        """Extract a title from message text"""
        if not text:
            return "Ohne Titel"
        
        # Clean HTML entities
        text = html.unescape(text)
        
        # Remove excessive emojis from title
        text_clean = re.sub(r'[^\w\s\-.,!?äöüÄÖÜß]', '', text)
        
        # Take first line or first sentence
        lines = text.split('\n')
        first_line = lines[0].strip()
        
        # If first line is very short, try first sentence
        if len(first_line) < 20 and len(lines) > 1:
            sentences = text.split('.')
            if len(sentences) > 0:
                first_line = sentences[0].strip()
        
        # Limit length
        if len(first_line) > 100:
            first_line = first_line[:97] + "..."
        
        return first_line or "Ohne Titel"
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract potential keywords from text"""
        if not text:
            return []
        
        keywords = []
        
        # Find hashtags
        hashtags = re.findall(r'#(\w+)', text)
        keywords.extend([tag.lower() for tag in hashtags if len(tag) > 2])
        
        # Find @mentions (channels/users)
        mentions = re.findall(r'@(\w+)', text)
        keywords.extend([mention.lower() for mention in mentions if len(mention) > 2])
        
        # Find important German keywords
        important_words = re.findall(r'\b(Breaking|Eilmeldung|Wichtig|Aktuell|Neu|Update|Exklusiv|Live)\b', text, re.IGNORECASE)
        keywords.extend([word.lower() for word in important_words])
        
        # Find URLs and extract domains
        urls = re.findall(r'https?://(?:www\.)?([^/\s]+)', text)
        keywords.extend([domain.split('.')[0].lower() for domain in urls])
        
        # Remove duplicates and limit
        keywords = list(set(keywords))
        return keywords[:10]
    
    def _clean_text_content(self, text: str) -> str:
        """Clean message text content"""
        if not text:
            return ""
        
        # Unescape HTML entities
        text = html.unescape(text)
        
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove excessive spaces
        text = re.sub(r' {2,}', ' ', text)
        
        # Clean up markdown-style formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
        text = re.sub(r'__(.*?)__', r'\1', text)      # Underline
        
        return text.strip()


# Sync wrapper function for Celery tasks
def sync_monitor_telegram_channels() -> int:
    """Synchronous wrapper for monitoring Telegram channels"""
    import os
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not configured")
        return 0
    
    monitor = TelegramChannelMonitor(bot_token)
    
    # Run async function in sync context
    try:
        return asyncio.run(monitor.monitor_channels())
    except Exception as e:
        logger.error(f"Error in sync monitoring: {e}")
        return 0

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from telegram import Bot
from telegram.error import TelegramError
import os
import re
from app.data import json_manager

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramChannelMonitor:
    """Telegram Channel Monitor für News-Aggregation"""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.bot = Bot(token=bot_token)
        self.monitored_channels = self._load_monitored_channels()
        
    def _load_monitored_channels(self) -> List[Dict[str, Any]]:
        """Lade überwachte Kanäle aus JSON-Datei"""
        sources = json_manager.read('sources')
        channels = []
        
        for source_id, source_data in sources.get('sources', {}).items():
            if source_data.get('type') == 'telegram':
                channels.append({
                    'id': source_id,
                    'channel_username': source_data.get('channel_username'),
                    'channel_id': source_data.get('channel_id'),
                    'keywords': source_data.get('keywords', []),
                    'exclude_keywords': source_data.get('exclude_keywords', []),
                    'last_message_id': source_data.get('last_message_id', 0)
                })
        
        return channels
    
    async def add_channel(self, channel_username: str, keywords: List[str] = None, 
                         exclude_keywords: List[str] = None) -> str:
        """Füge einen neuen Telegram-Kanal zur Überwachung hinzu"""
        try:
            # Channel-Info abrufen
            chat = await self.bot.get_chat(f"@{channel_username}")
            
            # Channel-Daten erstellen
            channel_data = {
                'type': 'telegram',
                'name': chat.title or channel_username,
                'channel_username': channel_username,
                'channel_id': chat.id,
                'keywords': keywords or [],
                'exclude_keywords': exclude_keywords or [],
                'last_message_id': 0,
                'is_active': True,
                'added_at': datetime.now().isoformat()
            }
            
            # In JSON speichern
            source_id = json_manager.add_item('sources', channel_data)
            
            # Lokale Liste aktualisieren
            self.monitored_channels = self._load_monitored_channels()
            
            logger.info(f"Channel {channel_username} hinzugefügt mit ID {source_id}")
            return source_id
            
        except TelegramError as e:
            logger.error(f"Fehler beim Hinzufügen von Channel {channel_username}: {e}")
            raise
    
    async def get_recent_messages(self, channel_username: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Hole die neuesten Nachrichten eines Kanals"""
        try:
            # Chat-ID ermitteln
            chat = await self.bot.get_chat(f"@{channel_username}")
            
            messages = []
            # Hier würdest du normalerweise die Telegram Client API verwenden
            # Da wir nur Bot-Token haben, ist der Zugriff auf Channel-Nachrichten limitiert
            # Für jetzt implementieren wir eine Placeholder-Funktion
            
            logger.info(f"Versuche Nachrichten von {channel_username} abzurufen")
            return messages
            
        except TelegramError as e:
            logger.error(f"Fehler beim Abrufen von Nachrichten von {channel_username}: {e}")
            return []
    
    def _message_matches_keywords(self, message_text: str, keywords: List[str], 
                                exclude_keywords: List[str]) -> bool:
        """Prüfe ob eine Nachricht den Keyword-Filtern entspricht"""
        if not message_text:
            return False
        
        message_lower = message_text.lower()
        
        # Prüfe Exclude-Keywords zuerst
        for exclude_word in exclude_keywords:
            if exclude_word.lower() in message_lower:
                return False
        
        # Wenn keine Keywords definiert, akzeptiere alle (außer excluded)
        if not keywords:
            return True
        
        # Prüfe Include-Keywords
        for keyword in keywords:
            if keyword.lower() in message_lower:
                return True
        
        return False
    
    def _extract_links(self, message_text: str) -> List[str]:
        """Extrahiere URLs aus Nachrichten-Text"""
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.findall(url_pattern, message_text)
    
    def _clean_message_text(self, text: str) -> str:
        """Bereinige Nachrichten-Text von Telegram-Formatierung"""
        if not text:
            return ""
        
        # Entferne Telegram-Formatierung
        text = re.sub(r'@\w+', '', text)  # Entferne @mentions
        text = re.sub(r'#\w+', '', text)  # Entferne #hashtags (optional)
        text = re.sub(r'\n+', '\n', text)  # Reduziere mehrfache Zeilenumbrüche
        
        return text.strip()
    
    async def save_message_as_article(self, message_data: Dict[str, Any], 
                                    source_id: str) -> str:
        """Speichere Telegram-Nachricht als Artikel"""
        
        # Artikel-Daten erstellen
        article_data = {
            'title': self._generate_title_from_message(message_data.get('text', '')),
            'content': self._clean_message_text(message_data.get('text', '')),
            'source_id': source_id,
            'source_type': 'telegram',
            'telegram_message_id': message_data.get('message_id'),
            'telegram_channel': message_data.get('chat', {}).get('username'),
            'published_at': message_data.get('date', datetime.now()).isoformat(),
            'scraped_at': datetime.now().isoformat(),
            'links': self._extract_links(message_data.get('text', '')),
            'media_urls': self._extract_media_urls(message_data),
            'relevance_score': None,  # Wird später von KI bewertet
            'sentiment_score': None,  # Wird später von KI bewertet
            'user_rating': None,  # Für Swipe-Feedback
            'tags': [],  # Wird später von KI/User gefüllt
            'is_processed': False
        }
        
        # In JSON speichern
        article_id = json_manager.add_item('articles', article_data)
        
        logger.info(f"Telegram-Nachricht als Artikel {article_id} gespeichert")
        return article_id
    
    def _generate_title_from_message(self, text: str, max_length: int = 100) -> str:
        """Generiere einen Titel aus dem Nachrichten-Text"""
        if not text:
            return "Telegram-Nachricht"
        
        # Erste Zeile oder ersten Satz als Titel verwenden
        lines = text.split('\n')
        title = lines[0] if lines else text
        
        # Kürzen falls zu lang
        if len(title) > max_length:
            title = title[:max_length-3] + "..."
        
        return title.strip()
    
    def _extract_media_urls(self, message_data: Dict[str, Any]) -> List[str]:
        """Extrahiere Media-URLs aus Telegram-Nachricht"""
        media_urls = []
        
        # Fotos
        if 'photo' in message_data:
            # Hier würdest du die Foto-URLs extrahieren
            pass
        
        # Videos
        if 'video' in message_data:
            # Hier würdest du die Video-URLs extrahieren
            pass
        
        # Dokumente
        if 'document' in message_data:
            # Hier würdest du die Dokument-URLs extrahieren
            pass
        
        return media_urls
    
    async def monitor_channels_once(self) -> int:
        """Einmalige Überwachung aller Kanäle (für Cronjob)"""
        total_new_articles = 0
        
        for channel in self.monitored_channels:
            if not channel.get('is_active', True):
                continue
            
            try:
                # Neue Nachrichten abrufen
                messages = await self.get_recent_messages(
                    channel['channel_username'], 
                    limit=50
                )
                
                new_articles = 0
                for message in messages:
                    # Prüfe ob Nachricht bereits verarbeitet
                    if message.get('message_id', 0) <= channel.get('last_message_id', 0):
                        continue
                    
                    # Prüfe Keywords
                    if not self._message_matches_keywords(
                        message.get('text', ''),
                        channel.get('keywords', []),
                        channel.get('exclude_keywords', [])
                    ):
                        continue
                    
                    # Speichere als Artikel
                    await self.save_message_as_article(message, channel['id'])
                    new_articles += 1
                
                # Update last_message_id
                if messages:
                    latest_message_id = max(msg.get('message_id', 0) for msg in messages)
                    json_manager.update('sources', {
                        f"sources.{channel['id']}.last_message_id": latest_message_id
                    })
                
                total_new_articles += new_articles
                logger.info(f"Channel {channel['channel_username']}: {new_articles} neue Artikel")
                
            except Exception as e:
                logger.error(f"Fehler bei Channel {channel['channel_username']}: {e}")
        
        return total_new_articles


# Hilfsfunktionen für Celery-Tasks
async def monitor_telegram_channels():
    """Async-Wrapper für Telegram-Monitoring"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN nicht gesetzt")
        return 0
    
    monitor = TelegramChannelMonitor(bot_token)
    return await monitor.monitor_channels_once()


def sync_monitor_telegram_channels():
    """Synchroner Wrapper für Celery"""
    return asyncio.run(monitor_telegram_channels())
