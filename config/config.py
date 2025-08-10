"""
App-Konfiguration für JSON-basierte News-Aggregator
"""

import os
from datetime import timedelta


class Config:
    # Flask Basis-Konfiguration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-me'
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = os.environ.get('DEBUG', 'true').lower() == 'true'
    
    # JSON Data Directory
    DATA_DIR = os.environ.get('DATA_DIR', '/app/data')
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')
    OPENAI_MAX_TOKENS = int(os.environ.get('OPENAI_MAX_TOKENS', '150'))
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    
    # Twitter Configuration (optional)
    TWITTER_BEARER_TOKEN = os.environ.get('TWITTER_BEARER_TOKEN')
    
    # Redis & Celery
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
    
    # App-spezifische Einstellungen
    MOBILE_FIRST = os.environ.get('MOBILE_FIRST', 'true').lower() == 'true'
    AUTO_BACKUP = os.environ.get('AUTO_BACKUP', 'true').lower() == 'true'
    BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', '7'))
    
    # Scraping Configuration
    SCRAPING_INTERVAL_MINUTES = int(os.environ.get('SCRAPING_INTERVAL_MINUTES', '30'))
    MAX_ARTICLES_PER_SOURCE = int(os.environ.get('MAX_ARTICLES_PER_SOURCE', '200'))
    CLEANUP_DAYS = int(os.environ.get('CLEANUP_DAYS', '3'))  # Standard: 3 Tage
    
    # Housekeeping Configuration
    HOUSEKEEPING_ENABLED = os.environ.get('HOUSEKEEPING_ENABLED', 'true').lower() == 'true'
    AUTO_CLEANUP_ARTICLES = os.environ.get('AUTO_CLEANUP_ARTICLES', 'true').lower() == 'true'
    AUTO_CLEANUP_MEDIA = os.environ.get('AUTO_CLEANUP_MEDIA', 'true').lower() == 'true'
    CLEANUP_SCHEDULE_CRON = os.environ.get('CLEANUP_SCHEDULE_CRON', '0 2 * * *')  # Daily at 2 AM
    
    # AI Configuration
    RELEVANCE_THRESHOLD = float(os.environ.get('RELEVANCE_THRESHOLD', '0.7'))
    SENTIMENT_ENABLED = os.environ.get('SENTIMENT_ENABLED', 'true').lower() == 'true'
    AUTO_TAGGING = os.environ.get('AUTO_TAGGING', 'true').lower() == 'true'
    
    # UI Configuration
    ARTICLES_PER_PAGE = int(os.environ.get('ARTICLES_PER_PAGE', '20'))
    SWIPE_SENSITIVITY = float(os.environ.get('SWIPE_SENSITIVITY', '0.3'))
    AUTO_REFRESH = os.environ.get('AUTO_REFRESH', 'false').lower() == 'true'


class DevelopmentConfig(Config):
    DEBUG = True
    FLASK_ENV = 'development'


class ProductionConfig(Config):
    DEBUG = False
    FLASK_ENV = 'production'
    # Produktionsspezifische Sicherheitseinstellungen
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


# Konfiguration basierend auf Umgebung
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config():
    return config[os.environ.get('FLASK_ENV', 'default')]
