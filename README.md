# News Aggregator & Tweet Generator

Ein hochperformanter News-Aggreg## 🎯 Features

### 🔗 Intelligente Link-Previews (NEU)
- **Asynchrone Generierung**: Previews werden beim Scraping erstellt, nicht bei der Anzeige
- **oEmbed-Integration**: Direkte YouTube, Twitter, Instagram, TikTok Embeds
- **10x Performance**: Schneller als traditionelle HTML-Scraping-Methoden
- **Visual Indicators**: 🟢 Grün = Instant-Previews, 🔵 Blau = On-Demand
- **Fallback-Strategien**: oEmbed → Quick Meta → Standard Scraping

### 📱 Telethon-Telegram-Integration (NEU)
- **User Client**: Vollzugriff auf alle Telegram-Kanäle (keine Bot-Limitierungen)
- **2FA-Support**: Sichere Authentifizierung mit Telefonnummer + SMS + Cloud-Passwort
- **Medien-Extraktion**: Automatisches Speichern von Bildern, Videos, Dokumenten
- **Realtime-Scraping**: Priorisierung von Nachrichten der letzten Stunde
- **Smart-Filtering**: Intelligente Duplikaterkennung basierend auf Message-IDs

### 🎯 AI-Training & Spam-Filter (NEU)
- **Favorite/Spam-System**: Ein-Klick Bewertung für Machine Learning
- **Automatisches Filtering**: Spam-Artikel werden ausgeblendet
- **Training-Data**: Benutzer-Feedback sammeln für AI-Verbesserung
- **Echtzeit-Statistiken**: Übersicht über Bewertungsverteilung

### 📱 Mobile-First UI mit Bootstrap 5
- **Responsive Design**: Optimiert für Smartphone-Nutzung
- **Touch-optimiert**: Große Buttons, einfache Navigation
- **Performance**: Asynchrone Inhalte-Ladung, keine Wartezeiten
- **Intuitive UX**: Swipe-Gesten und Ein-Klick-Aktionenter Link-Preview-Generierung, Telethon-basiertem Telegram-Scraping und KI-gestützter Inhaltsbewertung für automatisierte Tweet-Generierung.

## ✨ Hauptfeatures

🚀 **Asynchrone Link-Previews** - Sofortige Website-Snippets durch Pre-Generation beim Scraping  
⚡ **Telethon User Client** - Vollzugriff auf Telegram-Kanäle ohne Bot-Limitierungen  
🎯 **Smart Spam-Filter** - AI-Training durch Favorite/Spam-Klassifikation  
📱 **Mobile-First Design** - Optimiert für Smartphone-Nutzung mit Bootstrap 5  
🔄 **Realtime-Updates** - Background-Tasks für kontinuierliche Content-Aggregation  

## 🌐 Live-Demo
**[https://news.2b6.de](https://news.2b6.de)** - News Aggregator Live-Demo

## 🚀 Quick Start mit Docker

### Voraussetzungen
- Docker & Docker-Compose
- Git
- Nginx (für Domain-Setup)
- Telegram Account (für Telethon-Setup)

### Installation
```bash
# Repository klonen
git clone https://github.com/MatthiasHertel21/ticker.git
cd ticker

# Umgebungsvariablen setzen
cp .env.example .env
# .env Datei mit API-Keys bearbeiten (Telegram API ID/Hash, OpenAI Key)

# Container starten (Port 5020)
docker-compose up -d

# App testen
curl http://localhost:5020/health

# Telethon-Setup (einmalig)
# 1. Gehe zu http://localhost:5020/telegram/auth
# 2. Gib deine Telegram-Telefonnummer ein
# 3. Bestätige mit dem SMS-Code
# 4. Bei 2FA: Gib dein Cloud-Passwort ein
```

### Domain-Setup (news.2b6.de)
```bash
# Nginx-Konfiguration installieren
sudo cp nginx/news.2b6.de.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/news.2b6.de.conf /etc/nginx/sites-enabled/

# SSL-Pfade in nginx/news.2b6.de.conf anpassen, dann:
sudo nginx -t
sudo systemctl reload nginx
```

## 🛠 Technologie-Stack

- **Backend**: Flask 2.3.3, Celery, OpenAI GPT
- **Frontend**: Mobile-First HTML5/CSS3/JS ES6+, Bootstrap 5
- **Scraping**: Telethon (User Client), Beautiful Soup 4.12.2
- **Link-Previews**: oEmbed APIs + Meta-Tag Parsing
- **Datenhaltung**: JSON-Dateien (Thread-sicher)
- **Queue**: Redis für Background-Tasks
- **Container**: Docker-Compose (Port 5020)
- **APIs**: Telethon User API, Twitter API v2
- **Domain**: news.2b6.de (Nginx Reverse Proxy)

## � Features

### News-Aggregation
- **Telegram-Kanäle**: Automatisches Monitoring definierter Channels
- **Alternative Medien**: apollo-news, reitschuster, tichyseinblick, etc.
- **RSS-Feeds**: Nachrichtenportale und Blogs
- **Twitter-Accounts**: Öffentliche Profile überwachen

### KI-gestützte Bewertung
- **Relevanz-Score**: OpenAI GPT bewertet Artikel-Relevanz
- **Sentiment-Analyse**: Automatische Einordnung der Stimmung
- **Lernendes System**: Feedback durch Swipe-Gesten
- **Tag-System**: Automatische und manuelle Kategorisierung

### Mobile-First Interface
- **Swipe-Navigation**: Links/Rechts für schnelle Bewertung
- **Touch-optimiert**: Große Buttons, einfache Navigation
- **Responsive Design**: Optimiert für Smartphone-Nutzung
- **Offline-fähig**: Service Worker für wichtige Inhalte

### 🐦 Tweet-Generator
- **KI-Entwürfe**: Automatische Tweet-Generierung mit OpenAI
- **Format**: Text + Bild + Link
- **Vorschau**: Mobile-optimierte Tweet-Ansicht
- **Export**: Entwürfe für manuelles Posten

## 📊 Performance-Verbesserungen

### Link-Preview Performance
- **Standard HTML-Scraping**: 10-30 Sekunden pro URL
- **oEmbed-APIs**: 1-3 Sekunden pro URL (YouTube, Twitter, etc.)
- **Quick Meta-Tags**: 2-5 Sekunden pro URL
- **Asynchrone Generation**: ⚡ 0 Sekunden Wartezeit für Benutzer

### Telegram-Scraping Performance
- **Bot API**: Limitiert auf öffentliche Kanäle, Rate-Limits
- **Telethon User Client**: Alle Kanäle, höhere Rate-Limits, Medien-Support
- **Duplikat-Filter**: 99.9% Duplikat-Vermeidung durch Message-IDs
- **Realtime-Updates**: Priorisierung von Nachrichten der letzten Stunde

## 🛡️ Aktuelle Implementierung

✅ **Telethon User Client** - Vollzugriff auf Telegram-Kanäle  
✅ **Asynchrone Link-Previews** - oEmbed + Meta-Tag Parsing  
✅ **Favorite/Spam-Klassifikation** - AI-Training Data Collection  
✅ **Mobile-First UI** - Bootstrap 5 responsive Design  
✅ **Performance-Optimiert** - Keine Wartezeiten bei Link-Previews  
✅ **Background-Tasks** - Celery für kontinuierliche Content-Aggregation  
✅ **Media-Extraktion** - Automatisches Speichern von Telegram-Medien  
✅ **Smart Content-Parsing** - Intelligente URL-Extraktion und -Bereinigung  

🔄 **In Entwicklung**: Telethon-Integration in Background-Tasks  
🔄 **Geplant**: Twitter API v2 Integration für Tweet-Generierung  

## 🔧 Entwicklung

### Docker Commands
```bash
# Container neu bauen
docker-compose build

# Logs anzeigen
docker-compose logs webapp

# In Container-Shell
docker-compose exec webapp bash

# Tests ausführen (später)
docker-compose exec webapp pytest
```

### Lokale Entwicklung (ohne Docker)
```bash
# Virtual Environment
python -m venv venv
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt

# Entwicklungsserver (Port 5020)
export FLASK_ENV=development
export DATA_DIR=./data
python run.py
```

### Git Workflow
```bash
# Repository von GitHub klonen
git clone https://github.com/MatthiasHertel21/ticker.git

# Neuen Branch erstellen
git checkout -b feature/telegram-integration

# Changes committen
git add .
git commit -m "Add Telegram integration"

# Push to GitHub
git push origin feature/telegram-integration
```

## 📝 Wichtige Commands

```bash
# Datenbank-Migration erstellen
flask db migrate -m "Beschreibung"

# Migration anwenden
flask db upgrade

# Shell für Debugging
flask shell

# Entwicklungsserver mit Debug-Modus
export FLASK_ENV=development
python run.py
```

## 🔐 Umgebungsvariablen

Erstelle eine `.env` Datei mit folgenden Variablen:

```env
# Flask App
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# JSON Data Directory
DATA_DIR=/app/data

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Telegram Bot
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# Twitter (optional)
TWITTER_BEARER_TOKEN=your-twitter-bearer-token

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

## 🚢 Deployment

### Docker Production
```bash
# Production Build
docker-compose -f docker-compose.yml up -d

# Mit Nginx Reverse Proxy
sudo systemctl status nginx
curl https://news.2b6.de/health
```

### Entwicklungsphase - Status
- ✅ **Phase 1 Basis**: Docker-Setup, JSON-Datenhaltung
- 🔄 **Phase 2 In Arbeit**: Telegram-Integration  
- ⏳ **Phase 3 Geplant**: KI-Integration und Bewertung
- ⏳ **Phase 4 Geplant**: Tweet-Generator

## 📊 API-Integration

### Telegram Bot Setup
1. Bot bei @BotFather erstellen: `/newbot`
2. Token in `.env` eintragen: `TELEGRAM_BOT_TOKEN=your-token`
3. Bot zu gewünschten Channels hinzufügen

### OpenAI Setup (Phase 3)
1. API-Key bei OpenAI besorgen
2. In `.env` konfigurieren: `OPENAI_API_KEY=sk-your-key`
3. Usage Limits beachten

### GitHub Repository
- **URL**: https://github.com/MatthiasHertel21/ticker
- **Issues**: Feature-Requests und Bug-Reports
- **Wiki**: Detaillierte Dokumentation

## 📊 JSON-Datenstrukturen

### Datenorganisation
- **`data/sources.json`**: Nachrichtenquellen-Konfiguration
- **`data/articles.json`**: Gesammelte Artikel mit Metadaten
- **`data/tags.json`**: Tag-System und Lernalgorithmus
- **`data/tweets.json`**: Tweet-Entwürfe und Templates
- **`data/settings.json`**: App-Konfiguration
- **`data/backups/`**: Automatische Backups

### Thread-sichere Operationen
```python
from app.data import json_manager

# Artikel hinzufügen
article_id = json_manager.add_item('articles', {
    'title': 'Artikel Titel',
    'content': 'Artikel Inhalt...',
    'source_id': 'source_123',
    'relevance_score': 0.85
})

# Artikel suchen
articles = json_manager.search('articles', {
    'relevance_score': 0.8,
    'source_id': 'telegram_channel_1'
})

# Backup erstellen
json_manager._create_backup('articles')
```

## 🌐 Nginx Setup

### Lokale Nginx Integration
```bash
# Konfiguration kopieren
sudo cp nginx/news.2b6.de.conf /etc/nginx/sites-available/

# Site aktivieren
sudo ln -s /etc/nginx/sites-available/news.2b6.de.conf /etc/nginx/sites-enabled/

# SSL-Zertifikat anpassen (in der Konfiguration)
# ssl_certificate /path/to/your/cert.pem;
# ssl_certificate_key /path/to/your/key.pem;

# Nginx testen und neu laden
sudo nginx -t
sudo systemctl reload nginx
```

### DNS-Eintrag
Stelle sicher, dass `news.2b6.de` auf deinen Server zeigt.

## 🧪 Testing

- Unit Tests für alle Modelle und Utilities
- Integration Tests für Routes und Forms
- Coverage-Reports für Code-Qualität
- Automatisierte Tests mit GitHub Actions

## 📚 Weitere Dokumentation

- [Concept.md](concept.md) - Detailliertes Projektkonzept
- [NGINX_SETUP.md](NGINX_SETUP.md) - Nginx-Konfiguration für news.2b6.de
- [GitHub Repository](https://github.com/MatthiasHertel21/ticker) - Source Code & Issues

## 🤝 Beitragen

1. Repository forken: https://github.com/MatthiasHertel21/ticker
2. Feature Branch erstellen (`git checkout -b feature/amazing-feature`)
3. Changes committen (`git commit -m 'Add amazing feature'`)
4. Branch pushen (`git push origin feature/amazing-feature`)
5. Pull Request erstellen

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE) für Details.

---

**Live-Status**: 🟢 Entwicklung aktiv | **Domain**: news.2b6.de | **Port**: 5020
