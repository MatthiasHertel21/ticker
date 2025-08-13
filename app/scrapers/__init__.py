"""
Scrapers package initialization
"""

try:
    from .telegram_bot import TelegramChannelMonitor, sync_monitor_telegram_channels
except ImportError:
    TelegramChannelMonitor = None
    sync_monitor_telegram_channels = None

try:
    from .telethon_scraper import TelethonChannelScraper
except ImportError:
    TelethonChannelScraper = None

__all__ = ['TelegramChannelMonitor', 'sync_monitor_telegram_channels', 'TelethonChannelScraper']
