# News Aggregator & Tweet Generator - Konzept

## Projektübersicht
Ein hochperformanter News-Aggregator mit intelligenter Link-Preview-Generierung, Telethon-basiertem Telegram-Scraping und KI-gestützter Inhaltsbewertung für automatisierte Tweet-Generierung.

### Aktueller Status (August 2025)
**🎯 PRODUKTIV IM EINSATZ** - System läuft stabil auf https://news.2b6.de/

**Implementierte Features:**
- ✅ **Vollständiges Telegram-Scraping** mit Telethon (User API + Bot API Fallback)
- ✅ **Mobile-First UI** mit Bootstrap 5, responsive Design, sticky Navigation
- ✅ **JSON-basierte Datenhaltung** mit Thread-Safe JSON Manager  
- ✅ **Intelligente Link-Previews** (oEmbed + Meta-Tag Parsing)
- ✅ **Background Tasks** mit Celery + Redis (Auto-Scraping alle 30 Min)
- ✅ **Housekeeping-System** mit Storage-Management und Auto-Cleanup
- ✅ **Monitoring Dashboard** mit Live-Logs und Scraping-Statistiken
- ✅ **Docker-Deployment** (Multi-Container Setup)
- ✅ **Zeitzone-Management** (CET/CEST Support)
- ✅ **Media-Handling** für Telegram-Photos und -Videos
- ✅ **Artikel-Filtering** und Pagination (50/100/200 pro Seite)
- ✅ **Template-System** mit modularen Components

### Zielgruppe
- Einzelnutzer (persönliche Anwendung)
- Mobile-First Design für Smartphone-Nutzung
- Fokus auf alternative Medien und kritische Berichterstattung
- Echtzeitfähiges Content-Management mit Spam-Filtering

### Aktueller Technologie-Stack (Produktiv)
- **Backend**: Python Flask 2.3.3, Celery (Background Tasks)
- **Frontend**: HTML5, CSS3, JavaScript ES6+, Bootstrap 5 (Mobile-First)
- **Datenhaltung**: JSON-Dateien (Thread-Safe JSON-Manager)
- **Background Jobs**: Celery + Redis für Auto-Scraping
- **Template Engine**: Jinja2 mit Custom Filters & Blocks
- **Containerisierung**: Docker-Compose (Multi-Service Setup)
- **Web Scraping**: Telethon (User Client) + python-telegram-bot (Bot API)
- **Link Previews**: oEmbed APIs + BeautifulSoup Meta-Tag Parsing
- **Zeitzone**: pytz für CET/CEST Management
- **Monitoring**: Live-Logs, Storage-Stats, Scraping-Übersicht
- **Media**: Telegram Photo/Video Download & Storage

### Produktive Architektur
```
ticker/                          # 🎯 PRODUKTIVE ANWENDUNG
├── docker-compose.yml           # Multi-Container: webapp, celery, celery-beat, redis
├── Dockerfile                   # Flask App Container
├── nginx/                       # Reverse Proxy Setup
│   ├── news.2b6.de.conf        # Produktive Site-Config
│   └── setup-nginx.sh          # Auto-Setup Script
├── app/
│   ├── celery_app.py           # ✅ Celery-Integration mit Background Tasks
│   ├── data/
│   │   ├── json_manager.py     # ✅ Thread-Safe JSON Operations
│   │   ├── articles.json       # ✅ 200+ Artikel mit Link-Previews
│   │   ├── sources.json        # ✅ Telegram-Kanal-Konfiguration
│   │   ├── settings.json       # ✅ App-Einstellungen
│   │   ├── tweets.json         # 🔄 Tweet-Entwürfe (in Entwicklung)
│   │   └── backups/            # ✅ Automatische JSON-Backups
│   ├── routes/
│   │   ├── main.py             # ✅ Dashboard
│   │   ├── articles.py         # ✅ Artikel-Listing mit Pagination
│   │   ├── telegram.py         # ✅ Telegram-Kanal-Management
│   │   ├── monitoring.py       # ✅ Live-Logs & Scraping-Stats
│   │   ├── housekeeping.py     # ✅ Storage-Management & Cleanup
│   │   └── tweets.py           # 🔄 Tweet-Generator (geplant)
│   ├── scrapers/
│   │   ├── telethon_scraper.py # ✅ Hauptscraper (alle 30 Min)
│   │   ├── telegram_bot.py     # ✅ Bot API Fallback
│   │   └── rss_scraper.py      # 🔄 RSS-Support (optional)
│   ├── tasks/
│   │   ├── scraping_tasks.py   # ✅ Celery Auto-Scraping Tasks
│   │   └── housekeeping_tasks.py # ✅ Cleanup & Maintenance
│   ├── templates/
│   │   ├── base.html           # ✅ Responsive Layout mit Sticky Nav
│   │   ├── articles.html       # ✅ Mobile-First Artikel-Ansicht
│   │   ├── telegram.html       # ✅ Kanal-Management Interface
│   │   ├── scraping_logs.html  # ✅ Monitoring Dashboard
│   │   ├── dashboard.html      # ✅ Haupt-Dashboard
│   │   └── housekeeping/       # ✅ Storage-Management UI
│   ├── utils/
│   │   ├── timezone_utils.py   # ✅ CET/CEST Zeitzone-Management
│   │   ├── link_preview.py     # ✅ oEmbed + Meta-Tag Parsing
│   │   └── template_filters.py # ✅ Jinja2 Custom Filters
│   └── ai/                     # 🔄 KI-Integration (geplant)
│       ├── openai_client.py    # 🔄 GPT API Integration
│       └── tweet_generator.py  # 🔄 KI-basierte Tweet-Erstellung
├── config/
│   ├── config.py              # ✅ Umgebungsvariablen-Management
│   └── celery_config.py       # ✅ Celery-Konfiguration
├── data/                      # ✅ Persistente Daten (Docker Volume)
│   ├── articles.json          # ✅ ~200 Artikel mit Media
│   ├── sources.json           # ✅ 15+ Telegram-Kanäle
│   ├── backups/               # ✅ Tägliche Auto-Backups
│   └── media/                 # ✅ Telegram Photos/Videos
├── requirements.txt           # ✅ Alle Dependencies
├── .env.example              # ✅ Konfiguration Template
└── run.py                    # ✅ Flask Application Entry Point
│   │   ├── main.py         # Dashboard
│   │   ├── articles.py     # Artikel-Management mit Preview-API
│   │   ├── tasks.py        # Task-Management
│   │   └── telegram.py     # Telethon Authentication
│   ├── templates/          # Mobile-First Jinja2 Templates
│   │   ├── base.html       # Bootstrap 5 Layout
│   │   ├── articles.html   # Responsive Artikel-Display
│   │   ├── dashboard.html
│   │   ├── sources/
│   │   └── tweets/
│   ├── static/             # CSS, JS, Images
│   │   ├── css/
│   │   │   └── news-aggregator.css  # Custom Bootstrap 5 Theme
│   │   ├── js/
│   │   │   └── news-aggregator.js   # Interaktive Features
│   │   └── images/
│   ├── scrapers/           # Web-Scraping Module
│   │   ├── __init__.py
│   │   ├── telethon_scraper.py # Telethon User Client (Vollzugriff)
│   │   ├── telegram_bot.py     # Legacy Bot API
│   │   ├── twitter_scraper.py
│   │   ├── rss_scraper.py
│   │   └── web_scraper.py      # Für apollo, reitschuster, etc.
│   ├── utils/              # Utility-Module
│   │   ├── __init__.py
│   │   ├── link_preview.py     # Standard Link-Preview Generator
│   │   ├── oembed_preview.py   # Schnelle oEmbed + Meta-Tag Previews
│   │   └── template_filters.py # Jinja2 Custom Filters
│   ├── ai/                 # KI-Integration
│   │   ├── __init__.py
│   │   ├── openai_client.py
│   │   ├── sentiment.py    # Sentiment-Analyse
│   │   ├── relevance.py    # Relevanz-Bewertung (Favorite/Spam)
│   │   └── tweet_generator.py
│   └── tasks/              # Celery Background Tasks
│       ├── __init__.py
│       ├── scraping_tasks.py
│       └── ai_tasks.py
├── data/                   # Persistente JSON-Daten (Volume)
│   ├── sources.json
│   ├── articles.json       # Mit eingebetteten Link-Previews
│   ├── tags.json
│   ├── tweets.json
│   ├── media/              # Gespeicherte Telegram-Medien
│   ├── telethon_session.session  # Telethon Session File
│   └── backups/            # Automatische Backups
├── tests/                  # Unit Tests
├── config/
│   ├── config.py          # App-Konfiguration
│   └── celery_config.py   # Celery-Setup
├── requirements.txt        # Python Dependencies
├── .env.example           # Umgebungsvariablen Template
└── run.py                 # Application Entry Point
```
├── app/
│   ├── __init__.py          # Flask App Factory
│   ├── models/              # Datenbankmodelle
│   │   ├── __init__.py
│   │   ├── source.py        # Nachrichtenquellen
│   │   ├── article.py       # Gesammelte Artikel
│   │   ├── tag.py           # Tag-System
│   │   └── feedback.py      # User Feedback für ML
│   ├── routes/              # Route Handler
│   │   ├── __init__.py
│   │   ├── main.py          # Dashboard
│   │   ├── sources.py       # Quellen-Management
│   │   ├── articles.py      # Artikel-Ansicht
│   │   └── api.py           # API Endpoints
│   ├── services/            # Business Logic
│   │   ├── __init__.py
│   │   ├── telegram_collector.py
│   │   ├── rss_collector.py
│   │   ├── web_scraper.py
│   │   ├── ai_evaluator.py
│   │   └── tweet_generator.py
│   ├── templates/           # Mobile-First Templates
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── sources/
│   │   ├── articles/
│   │   └── components/
│   ├── static/              # CSS, JS, Images
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── utils/               # Hilfsfunktionen
│       ├── __init__.py
│       └── date_helpers.py
├── celery_app/              # Background Tasks
├── migrations/              # Datenbankmigrationen
├── tests/                   # Unit Tests
├── config.py               # Konfiguration
├── requirements.txt        # Python Dependencies
├── run.py                  # Application Entry Point
└── .env                    # API Keys & Secrets
```

### Kernfunktionalitäten

#### 1. Intelligente Link-Previews (NEU)
- **Asynchrone Generierung**: Link-Previews werden beim Scraping erstellt, nicht bei der Anzeige
- **oEmbed-Integration**: Direkte YouTube, Twitter, Instagram, TikTok Embeds
- **Meta-Tag-Parsing**: Schnelle OpenGraph & Twitter Cards Extraktion
- **Performance**: 10x schneller als traditionelle Scraping-Methoden
- **Fallback-Strategien**: oEmbed → Quick Meta → Standard Scraping
- **Visual Indicators**: Grüne Buttons für Instant-Previews, blaue für On-Demand

#### 2. Telethon-basiertes Telegram-Scraping
- **User Client**: Vollzugriff auf Telegram-Kanäle (keine Bot-Limitierungen)
- **2FA-Support**: Sichere Authentifizierung mit Telefonnummer + Code
- **Medien-Extraktion**: Bilder, Videos, Dokumente automatisch gespeichert
- **Realtime-Scraping**: Nachrichten der letzten Stunde priorisiert
- **Duplikatsschutz**: Intelligente ID-basierte Filterung

#### 3. Favorite/Spam-Klassifikationssystem
- **AI-Training-Data**: Benutzer-Feedback für Machine Learning
- **Spam-Filtering**: Automatische Ausblendung bewerteter Spam-Artikel
- **Interaktive Bewertung**: Ein-Klick Favorite/Spam Buttons
- **Statistiken**: Echtzeit-Übersicht über Bewertungsverteilung

#### 4. Mobile-First UI mit Bootstrap 5
- **Responsive Design**: Optimiert für Smartphone-Nutzung
- **Performance-Optimiert**: Asynchrone Inhalte-Ladung
- **Intuitive Navigation**: Swipe-Gesten und Touch-optimierte Buttons
- **Dark/Light Theme**: Automatische Anpassung an System-Präferenzen

#### 5. Erweiterte Content-Verwaltung
- **Template-Filter**: Intelligente Telegram-Markup-Bereinigung
- **URL-Extraktion**: Automatische Link-Erkennung und -Verarbeitung
- **Media-Integration**: Eingebettete Bilder und Videos aus Telegram
- **Content-Truncation**: Smart Preview mit "Mehr anzeigen" Funktionalität

#### 6. Quellenmanagement
- **Telegram-Kanäle**: Integration über Telethon User Client
- **RSS-Feeds**: Zeitungen, Blogs, alternative Medien
- **Web-Scraping**: Spezielle Webseiten (Apollo, Reitschuster, Tichy, etc.)
- **Wissenschaftliche Quellen**: Papers, Studien
- CRUD-Operationen für alle Quellentypen
- Filter- und Suchkriterien pro Quelle

#### 7. News-Aggregation (Automatisiert)
- **Telethon Collector**: Überwacht definierte Kanäle mit Vollzugriff
- **RSS Collector**: Mehrmals täglich Feeds abfragen
- **Web Scraper**: Strukturierte Datenextraktion
- Duplikaterkennung und -vermeidung
- Metadaten-Extraktion (Datum, Autor, Tags, Medien)

#### 8. KI-basierte Bewertung
- **OpenAI Integration**: GPT API für Content-Analyse
### Kernfunktionalitäten (Implementierungsstatus)

#### 1. ✅ Telegram-Scraping (PRODUKTIV)
- **Telethon User API**: Vollständiger Zugang zu allen Kanälen
- **Bot API Fallback**: Backup-System bei API-Limits
- **Auto-Scraping**: Alle 30 Minuten via Celery Tasks
- **Media-Download**: Automatischer Download von Photos/Videos
- **Duplikat-Erkennung**: Verhindert doppelte Artikel
- **Rate-Limiting**: Respektiert Telegram API-Limits

#### 2. ✅ Intelligente Link-Previews (PRODUKTIV)
- **oEmbed-Support**: YouTube, Twitter, Instagram, etc.
- **Meta-Tag-Parsing**: Titel, Beschreibung, Bilder
- **Asynchrone Verarbeitung**: Keine UI-Blockierung
- **Fallback-Strategien**: Bei fehlgeschlagenen Previews
- **Caching**: Vermeidung wiederholter Requests

#### 3. ✅ Mobile-First UI (PRODUKTIV)
- **Responsive Design**: Bootstrap 5 mit Custom CSS
- **Touch-Optimiert**: Swipe-Gesten und Touch-Navigation
- **Sticky Navigation**: Immer verfügbare Hauptnavigation
- **Artikel-Pagination**: 50/100/200 Artikel pro Seite
- **Live-Updates**: JavaScript-basierte Aktualisierungen

#### 4. ✅ Housekeeping & Monitoring (PRODUKTIV)
- **Storage-Management**: Übersicht über Datenvolumen
- **Auto-Cleanup**: Alte Artikel und verwaiste Media-Dateien
- **Backup-System**: Automatische JSON-Backups
- **Live-Monitoring**: Scraping-Logs in Echtzeit
- **Statistiken**: Artikel-Counts, Speicherverbrauch

#### 5. ✅ Background Processing (PRODUKTIV)
- **Celery Workers**: Parallele Task-Verarbeitung
- **Redis Queue**: Zuverlässige Message Queue
- **Scheduled Tasks**: Celery-Beat für wiederkehrende Jobs
- **Error Handling**: Robust gegen API-Ausfälle

#### 6. 🔄 KI-Integration (GEPLANT - NÄCHSTER SCHRITT)
- **OpenAI GPT API**: Content-Klassifikation und -Bewertung
- **Relevanz-Scoring**: Automatische Bewertung für Tweet-Eignung
- **Sentiment-Analyse**: Positiv/Negativ/Neutral Klassifikation
- **Tag-Generierung**: Automatisches Tagging nach Themen
- **Lernfähigkeit**: Feedback-basierte Verbesserung

#### 7. 🔄 Tweet-Generator (GEPLANT - NÄCHSTER SCHRITT)
- **KI-Entwürfe**: GPT-generierte Tweet-Texte
- **Bild-Integration**: Automatische Bildauswahl aus Artikeln
- **Vorschau-System**: Live-Vorschau des finalen Tweets
- **One-Click-Export**: Kopieren für manuelles Posten
- **Template-System**: Verschiedene Tweet-Stile

### Performance & Sicherheit (Produktiver Stand)

#### Performance-Optimierungen ✅
- **Asynchrone Link-Previews**: Keine Wartezeiten bei der Anzeige
- **Thread-Safe JSON**: Parallele Lese-/Schreibzugriffe möglich
- **Celery Background Tasks**: CPU-intensive Aufgaben ausgelagert
- **Smart Content-Loading**: Pagination mit konfigurierbaren Limits
- **Media-Caching**: Lokale Speicherung von Telegram-Medien
- **Zeitzone-optimiert**: CET/CEST für korrekte Zeitstempel

#### Sicherheitsaspekte ✅
- **Telethon Session-Verschlüsselung**: Sichere API-Authentifizierung
- **Input-Validierung**: Schutz vor fehlerhaften Daten
- **Error-Handling**: Robuste Fehlerbehandlung in allen Komponenten
- **Docker-Isolation**: Container-basierte Sicherheit
- **Auto-Cleanup**: Verhindert unbegrenztes Datenwachstum

### Aktuelle Deployment-Konfiguration ✅
- **Produktion**: Docker-Compose Multi-Container Setup
- **Services**: webapp, celery, celery-beat, redis
- **Port**: 5020 (extern verfügbar)
- **Domain**: https://news.2b6.de/
- **SSL**: Nginx Reverse Proxy mit SSL-Terminierung
- **Monitoring**: Live-Logs über /monitoring/
- **Backup**: Automatische JSON-Backups

---

## 🎯 NÄCHSTER IMPLEMENTIERUNGSSCHRITT: KI-TWEET-GENERATOR

### Ziel-Features für nächste Entwicklungsphase:

#### Phase 1: OpenAI Integration (Woche 1-2)
1. **OpenAI API Setup**
   - API-Key-Konfiguration in .env
   - GPT-Client-Wrapper implementieren
   - Rate-Limiting und Error-Handling

2. **Content-Analyse-Engine**
   - Artikel-Relevanz-Scoring (0-100 Punkte)
   - Sentiment-Analyse (positiv/neutral/negativ)
   - Automatische Tag-Generierung
   - Tweet-Tauglichkeits-Bewertung

#### Phase 2: Tweet-Generator (Woche 3-4)
1. **Tweet-Generierung**
   - Multiple Tweet-Varianten pro Artikel
   - Verschiedene Ton-Stile (informativ, kontrovers, neutral)
   - Automatische Hashtag-Generierung
   - Link-Integration mit Kurz-URLs

2. **UI-Integration**
   - Tweet-Generator-Seite (/tweets/)
   - Live-Vorschau der generierten Tweets
   - Artikel-Filter nach AI-Score
   - One-Click-Kopieren für Social Media

#### Phase 3: Machine Learning (Woche 5-6)
1. **Feedback-System**
   - User-Bewertung für generierte Tweets
   - Lernendes System basierend auf Feedback
   - A/B-Testing verschiedener Prompts

2. **Analytics & Optimierung**
   - Tweet-Performance-Tracking
   - Erfolgsrate-Analyse
   - Automatische Prompt-Optimierung

### Technische Implementierung:

#### Neue Dateien:
```
app/ai/
├── __init__.py
├── openai_client.py        # GPT API Wrapper
├── content_analyzer.py     # Artikel-Analyse
├── tweet_generator.py      # Tweet-Erstellung
└── prompt_templates.py     # GPT Prompts

app/routes/
└── tweets.py              # Tweet-Management Routes

app/templates/tweets/
├── generator.html         # Tweet-Generator UI
├── preview.html          # Tweet-Vorschau
└── analytics.html        # Performance-Analytics
```

#### Konfiguration:
- OpenAI API Key in .env
- GPT Model Selection (GPT-3.5/GPT-4)
- Rate-Limiting Konfiguration
- Tweet-Template-System

#### Datenstrukturen:
```json
{
  "tweet_drafts": [
    {
      "id": "uuid",
      "article_id": "article_uuid",
      "generated_text": "Tweet-Text...",
      "style": "informativ|kontrovers|neutral",
      "ai_score": 85,
      "sentiment": "neutral",
      "hashtags": ["#news", "#politik"],
      "created_at": "2025-08-10T14:30:00+02:00",
      "user_rating": null,
      "used": false
    }
  ]
}
```

### Erfolgskriterien:
- [ ] 90%+ der Artikel erhalten AI-Relevanz-Score
- [ ] 3+ Tweet-Varianten pro relevantem Artikel
- [ ] Sub-3-Sekunden Response-Zeit für Tweet-Generierung
- [ ] Integration in bestehende UI ohne Performance-Verlust
- [ ] Kosten unter 5€/Monat für OpenAI API

### Zeitplan:
- **Woche 1**: OpenAI Setup + Content-Analyzer
- **Woche 2**: Tweet-Generator Backend
- **Woche 3**: UI-Integration + Preview-System
- **Woche 4**: Testing + Optimierung
- **Woche 5**: Feedback-System
- **Woche 6**: Analytics + Machine Learning

**Start-Datum**: 12. August 2025  
**Ziel-Completion**: 23. September 2025
