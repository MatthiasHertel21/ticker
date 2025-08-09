# News Aggregator & Tweet Generator - Konzept

## Projektübersicht
Ein hochperformanter News-Aggregator mit intelligenter Link-Preview-Generierung, Telethon-basiertem Telegram-Scraping und KI-gestützter Inhaltsbewertung für automatisierte Tweet-Generierung.

### Zielgruppe
- Einzelnutzer (persönliche Anwendung)
- Mobile-First Design für Smartphone-Nutzung
- Fokus auf alternative Medien und kritische Berichterstattung
- Echtzeitfähiges Content-Management mit Spam-Filtering

### Technologie-Stack
- **Backend**: Python Flask 2.3.3, Celery (Background Tasks)
- **Frontend**: HTML5, CSS3, JavaScript ES6+, Bootstrap 5 (Mobile-First)
- **Datenhaltung**: JSON-Dateien (File-basiert mit Thread-Safety)
- **Data Management**: Custom JSON-Manager mit Threading-Locks
- **Template Engine**: Jinja2 mit Custom Filters
- **Formulare**: Flask-WTF
- **KI-Integration**: OpenAI GPT API für Content-Klassifikation
- **Message Queue**: Redis (für Celery Background Tasks)
- **Containerisierung**: Docker & Docker-Compose (Port 5020)
- **Web Scraping**: Telethon (User Client), Beautiful Soup 4.12.2
- **Link Previews**: oEmbed APIs + Meta-Tag Parsing für sofortige Website-Snippets
- **APIs**: Telethon User API (Telegram), Twitter API v2

### Projektstruktur
```
ticker/
├── docker-compose.yml       # Container-Orchestrierung (Port 5020)
├── Dockerfile              # Flask App Container
├── nginx/                  # Nginx-Konfiguration
│   └── news.2b6.de.conf   # Site-Config für lokalen Nginx
├── app/
│   ├── __init__.py         # Flask App Factory
│   ├── data/               # JSON-Datenhaltung
│   │   ├── __init__.py
│   │   ├── json_manager.py # Thread-Safe JSON Manager
│   │   ├── sources.json    # Nachrichtenquellen
│   │   ├── articles.json   # Gesammelte Artikel mit Link-Previews
│   │   ├── tags.json       # Tag-System
│   │   ├── tweets.json     # Tweet-Entwürfe
│   │   └── settings.json   # App-Einstellungen
│   ├── models/             # Python-Datenmodelle (ohne DB)
│   │   ├── __init__.py
│   │   ├── source.py       # Source-Klasse
│   │   ├── article.py      # Article-Klasse mit Media Support
│   │   ├── tag.py          # Tag-Klasse
│   │   └── tweet_draft.py  # TweetDraft-Klasse
│   ├── routes/             # Route Handler
│   │   ├── __init__.py
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
- **Relevanz-Scoring**: Automatische Bewertung für Tweet-Eignung
- **Sentiment-Analyse**: Positiv/Negativ/Neutral
- **Tag-Generierung**: Automatisches Tagging nach Themen
- **Lernfähigkeit**: Feedback-basierte Verbesserung

#### 9. Tweet-Generator
- **Entwurfs-Erstellung**: KI-generierte Tweet-Texte
- **Bild-Integration**: Automatische Bildauswahl aus Artikel
- **Link-Shortening**: Für Quellenangaben
- **Vorschau**: Wie der Tweet aussehen würde
- **One-Click Kopieren**: Für manuelles Posten

### Performance-Optimierungen
- **Asynchrone Link-Previews**: Keine Wartezeiten bei der Anzeige
- **Parallele Preview-Generierung**: Bis zu 3 Links pro Artikel gleichzeitig
- **Caching-Strategien**: Redis für Background-Tasks
- **Smart Content-Loading**: Nur benötigte Inhalte laden
- **Optimierte JSON-Performance**: Thread-safe File-Management

### Sicherheitsaspekte
- CSRF-Schutz durch Flask-WTF
- Sichere Session-Cookies
- Input-Validierung und Sanitization
- Rate-Limiting für API-Requests
- Telethon Session-Verschlüsselung

### Entwicklungsworkflow
1. Docker-Environment starten (Port 5020)
2. Telethon-Authentifizierung einrichten
3. Telegram-Kanäle konfigurieren
4. Background-Tasks aktivieren
5. Link-Preview-System testen

### Deployment-Optionen
- **Entwicklung**: Docker-Compose mit Hot-Reload
- **Staging/Produktion**: Gunicorn + Nginx
- **Container**: Docker
- **Cloud**: Heroku, AWS, DigitalOcean

### Erweiterungsmöglichkeiten
- Caching (Redis)
- Background Tasks (Celery)
- Logging und Monitoring
- API Rate Limiting
- Internationalisierung (i18n)
- WebSocket-Support (Flask-SocketIO)

### Testing-Strategie
- Unit Tests für Modelle und Utilities
- Integration Tests für Routes
- Frontend Tests (optional: Selenium)
- Test Coverage Reporting

### Performance-Optimierungen
- Database Query Optimization
- Static File Caching
- Gzip Compression
- CDN für Static Assets
- Database Connection Pooling

## Nächste Schritte
1. Projekt-Setup und virtuelle Umgebung
2. Basis Flask-Anwendung erstellen
3. Datenbankmodelle definieren
4. Authentifizierungssystem implementieren
5. Basis-Templates und Routes erstellen
6. Testing-Framework einrichten
7. Deployment-Konfiguration
