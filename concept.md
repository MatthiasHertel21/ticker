# News Aggregator & Tweet Generator - Konzept

## Projektübersicht
Ein persönlicher News-Aggregator für kritische Twitter-Beiträge mit KI-gestützter Inhaltsbewertung und automatisierter Tweet-Generierung.

### Zielgruppe
- Einzelnutzer (persönliche Anwendung)
- Mobile-First Design für Smartphone-Nutzung
- Fokus auf alternative Medien und kritische Berichterstattung

### Technologie-Stack
- **Backend**: Python Flask, Celery (Background Tasks)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap (Mobile-First)
- **Datenhaltung**: JSON-Dateien (File-basiert)
- **Data Management**: Custom JSON-Manager mit Threading-Locks
- **Template Engine**: Jinja2
- **Formulare**: Flask-WTF
- **KI-Integration**: OpenAI GPT API
- **Message Queue**: Redis (für Celery)
- **Containerisierung**: Docker & Docker-Compose (Port 5020)
- **Web Scraping**: BeautifulSoup, Scrapy
- **APIs**: Telegram Bot API, Twitter API v2

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
│   │   ├── json_manager.py # JSON-File Manager
│   │   ├── sources.json    # Nachrichtenquellen
│   │   ├── articles.json   # Gesammelte Artikel
│   │   ├── tags.json       # Tag-System
│   │   ├── tweets.json     # Tweet-Entwürfe
│   │   └── settings.json   # App-Einstellungen
│   ├── models/             # Python-Datenmodelle (ohne DB)
│   │   ├── __init__.py
│   │   ├── source.py       # Source-Klasse
│   │   ├── article.py      # Article-Klasse
│   │   ├── tag.py          # Tag-Klasse
│   │   └── tweet_draft.py  # TweetDraft-Klasse
│   ├── routes/             # Route Handler
│   │   ├── __init__.py
│   │   ├── main.py         # Dashboard
│   │   ├── sources.py      # Quellen-Management
│   │   ├── articles.py     # Artikel-Ansicht
│   │   └── tweets.py       # Tweet-Generator
│   ├── templates/          # Mobile-First Jinja2 Templates
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── articles/
│   │   ├── sources/
│   │   └── tweets/
│   ├── static/             # CSS, JS, Images
│   │   ├── css/
│   │   │   └── mobile.css  # Mobile-optimiert
│   │   ├── js/
│   │   │   └── swipe.js    # Swipe-Gesten für Bewertung
│   │   └── images/
│   ├── scrapers/           # Web-Scraping Module
│   │   ├── __init__.py
│   │   ├── telegram_bot.py # Telegram Channel Scraper
│   │   ├── twitter_scraper.py
│   │   ├── rss_scraper.py
│   │   └── web_scraper.py  # Für apollo, reitschuster, etc.
│   ├── ai/                 # KI-Integration
│   │   ├── __init__.py
│   │   ├── openai_client.py
│   │   ├── sentiment.py    # Sentiment-Analyse
│   │   ├── relevance.py    # Relevanz-Bewertung
│   │   └── tweet_generator.py
│   └── tasks/              # Celery Background Tasks
│       ├── __init__.py
│       ├── scraping_tasks.py
│       └── ai_tasks.py
├── data/                   # Persistente JSON-Daten (Volume)
│   ├── sources.json
│   ├── articles.json
│   ├── tags.json
│   ├── tweets.json
│   └── backups/            # Automatische Backups
├── tests/                  # Unit Tests
├── config/
│   ├── config.py          # App-Konfiguration
│   └── celery_config.py   # Celery-Setup
├── requirements.txt        # Python Dependencies
├── .env.example           # Umgebungsvariablen Template
└── run.py                 # Application Entry Point
```
```
ticker/
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

#### 1. Quellenmanagement
- **Telegram-Kanäle**: Integration über Telegram Bot API
- **RSS-Feeds**: Zeitungen, Blogs, alternative Medien
- **Web-Scraping**: Spezielle Webseiten (Apollo, Reitschuster, Tichy, etc.)
- **Wissenschaftliche Quellen**: Papers, Studien
- CRUD-Operationen für alle Quellentypen
- Filter- und Suchkriterien pro Quelle

#### 2. News-Aggregation (Automatisiert)
- **Telegram Collector**: Überwacht definierte Kanäle
- **RSS Collector**: Mehrmals täglich Feeds abfragen
- **Web Scraper**: Strukturierte Datenextraktion
- Duplikaterkennung und -vermeidung
- Metadaten-Extraktion (Datum, Autor, Tags)

#### 3. KI-basierte Bewertung
- **OpenAI Integration**: GPT API für Content-Analyse
- **Relevanz-Scoring**: Automatische Bewertung für Tweet-Eignung
- **Sentiment-Analyse**: Positiv/Negativ/Neutral
- **Tag-Generierung**: Automatisches Tagging nach Themen
- **Lernfähigkeit**: Feedback-basierte Verbesserung

#### 4. Mobile Dashboard
- **Swipe-Interface**: Links/Rechts für Feedback
- **Filterbare Liste**: Nach Datum, Quelle, Tags, Score
- **Suchfunktion**: Volltext, Personen, Schlagwörter
- **Detailansicht**: Artikel mit Metadaten und Originallink

#### 5. Tweet-Generator
- **Entwurfs-Erstellung**: KI-generierte Tweet-Texte
- **Bild-Integration**: Automatische Bildauswahl aus Artikel
- **Link-Shortening**: Für Quellenangaben
- **Vorschau**: Wie der Tweet aussehen würde
- **One-Click Kopieren**: Für manuelles Posten

### Sicherheitsaspekte
- CSRF-Schutz durch Flask-WTF
- Sichere Session-Cookies
- Passwort-Hashing (bcrypt)
- Input-Validierung
- SQL-Injection Schutz durch SQLAlchemy

### Entwicklungsworkflow
1. Virtuelle Umgebung einrichten
2. Dependencies installieren
3. Datenbank initialisieren
4. Entwicklungsserver starten
5. Tests ausführen

### Deployment-Optionen
- **Entwicklung**: Flask Development Server
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
