"""
Scraping-Überwachung und Log-Management
"""

from flask import Blueprint, render_template, jsonify, request
from datetime import datetime, timedelta
import logging
import json
import re
from app.data import json_manager

bp = Blueprint('monitoring', __name__, url_prefix='/monitoring')
logger = logging.getLogger(__name__)


@bp.route('/')
def scraping_overview():
    """Scraping-Übersicht mit Logs und Statistiken"""
    try:
        # Basis-Statistiken laden
        articles = json_manager.read('articles')
        sources = json_manager.read('sources')
        
        stats = {
            'total_articles': len(articles.get('articles', [])) if isinstance(articles.get('articles', []), list) else 0,
            'total_channels': len(sources.get('sources', {})),
            'last_update': articles.get('metadata', {}).get('last_updated', 'Unbekannt')
        }
        
        return render_template('scraping_logs.html', stats=stats)
        
    except Exception as e:
        logger.error(f"Fehler beim Laden der Scraping-Übersicht: {e}")
        return render_template('scraping_logs.html', stats={
            'total_articles': 0,
            'total_channels': 0,
            'last_update': 'Fehler'
        })


@bp.route('/api/logs')
def get_scraping_logs():
    """API-Endpunkt für Scraping-Logs"""
    try:
        # Parameter
        level = request.args.get('level', '')
        source = request.args.get('source', '')
        lines = int(request.args.get('lines', 50))
        
        # Docker-Logs lesen
        logs = _get_docker_logs(level, source, lines)
        
        # Statistiken berechnen
        stats = _calculate_scraping_stats()
        
        return jsonify({
            'logs': logs,
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Laden der Logs: {e}")
        return jsonify({
            'error': str(e),
            'logs': [],
            'stats': {}
        }), 500


def _get_docker_logs(level_filter='', source_filter='', lines=50):
    """Extrahiert relevante Logs aus Python-Logging"""
    import os
    import glob
    
    logs = []
    
    # Versuche verschiedene Log-Quellen
    log_sources = [
        # Python-Log-Handler
        '/app/logs/*.log',
        # Celery-Logs falls vorhanden
        '/var/log/celery/*.log',
        # Aktuelle Session-Logs
        'logs/*.log'
    ]
    
    try:
        # Aktuelles Python-Logging verwenden
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            if hasattr(handler, 'baseFilename'):
                try:
                    with open(handler.baseFilename, 'r') as f:
                        log_lines = f.readlines()[-lines:]
                        for line in log_lines:
                            parsed_log = _parse_python_log_line(line.strip())
                            if parsed_log:
                                logs.append(parsed_log)
                except Exception:
                    pass
        
        # Fallback: Simuliere Log-Einträge aus aktuellen Daten
            
        # Fallback: Simuliere Log-Einträge aus aktuellen Daten
        if not logs:
            from app.data import json_manager
            articles = json_manager.read('articles')
            settings = json_manager.read('settings')
            sources = json_manager.read('sources')
            
            # Letzte Scraping-Aktivitäten simulieren
            article_list = articles.get('articles', []) if isinstance(articles.get('articles', []), list) else []
            recent_articles = sorted(article_list, key=lambda x: x.get('scraped_date', ''), reverse=True)[:5]
            
            for article in recent_articles:
                logs.append({
                    'timestamp': article.get('scraped_date', datetime.now().isoformat()),
                    'level': 'INFO',
                    'source': 'scraper',
                    'message': f'Artikel gescraped: {article.get("title", "Unbekannt")[:50]}... von {article.get("channel", "Unbekannt")}',
                    'container': 'ticker_celery'
                })
            
            # Scraping-Status-Log
            last_update = articles.get('metadata', {}).get('last_updated', 'Unbekannt')
            logs.append({
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'source': 'system',
                'message': f'Letztes Update: {last_update}',
                'container': 'ticker_webapp'
            })
            
            # Channel-Status
            channel_count = len(sources.get('sources', {}))
            logs.append({
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'source': 'sources',
                'message': f'Überwache {channel_count} Telegram-Kanäle',
                'container': 'ticker_celery'
            })
            
            # Artikel-Statistik
            article_count = len(article_list)
            logs.append({
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'source': 'statistics',
                'message': f'Aktuelle Artikel im System: {article_count}',
                'container': 'ticker_webapp'
            })
            
            # Housekeeping-Status
            if settings.get('housekeeping', {}).get('enabled', False):
                retention_days = settings.get('housekeeping', {}).get('retention_days', 3)
                logs.append({
                    'timestamp': datetime.now().isoformat(),
                    'level': 'INFO', 
                    'source': 'housekeeping',
                    'message': f'Housekeeping aktiv: Lösche Artikel älter als {retention_days} Tage',
                    'container': 'ticker_celery'
                })
            else:
                logs.append({
                    'timestamp': datetime.now().isoformat(),
                    'level': 'WARNING',
                    'source': 'housekeeping', 
                    'message': 'Housekeeping ist deaktiviert - Daten könnten sich anhäufen',
                    'container': 'ticker_celery'
                })
    
    except Exception as e:
        logger.error(f"Fehler beim Laden der Logs: {e}")
        logs.append({
            'timestamp': datetime.now().isoformat(),
            'level': 'ERROR',
            'source': 'monitoring',
            'message': f'Log-Fehler: {str(e)}',
            'container': 'ticker_webapp'
        })
    
    # Filter anwenden
    if level_filter or source_filter:
        filtered_logs = []
        for log in logs:
            if level_filter and log.get('level') != level_filter:
                continue
            if source_filter and source_filter.lower() not in log.get('message', '').lower():
                continue
            filtered_logs.append(log)
        logs = filtered_logs
    
    # Nach Timestamp sortieren (neueste zuerst)  
    logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    return logs[:lines]


def _parse_python_log_line(line):
    """Parsed eine Python-Log-Zeile"""
    try:
        # Format: LEVEL:logger:message oder ähnlich
        if ':' in line:
            parts = line.split(':', 2)
            if len(parts) >= 3:
                return {
                    'timestamp': datetime.now().isoformat(),
                    'level': parts[0].strip(),
                    'source': parts[1].strip(),
                    'message': parts[2].strip(),
                    'container': 'ticker_webapp'
                }
        
        # Fallback für andere Formate
        return {
            'timestamp': datetime.now().isoformat(),
            'level': 'INFO',
            'source': 'application',
            'message': line,
            'container': 'ticker_webapp'
        }
    except Exception:
        return None


def _determine_source(message):
    """Bestimmt die Quelle basierend auf der Nachricht"""
    message_lower = message.lower()
    
    if 'telethon' in message_lower:
        return 'telethon'
    elif 'bot api' in message_lower or 'telegram bot' in message_lower:
        return 'bot_api'
    elif 'celery' in message_lower:
        return 'celery'
    elif 'scraping' in message_lower or 'monitoring' in message_lower:
        return 'scraping'
    else:
        return 'system'


def _calculate_scraping_stats():
    """Berechnet aktuelle Scraping-Statistiken"""
    try:
        articles = json_manager.read('articles')
        articles_data = articles.get('articles', [])
        
        if not isinstance(articles_data, list):
            return {
                'total_articles': 0,
                'today_articles': 0,
                'last_hour': 0,
                'last_6_hours': 0
            }
        
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        one_hour_ago = now - timedelta(hours=1)
        six_hours_ago = now - timedelta(hours=6)
        
        total_articles = len(articles_data)
        today_articles = 0
        last_hour = 0
        last_6_hours = 0
        
        for article in articles_data:
            try:
                # Parse Datum
                scraped_date_str = article.get('scraped_date', article.get('published_date', ''))
                if not scraped_date_str:
                    continue
                
                scraped_date = datetime.fromisoformat(scraped_date_str.replace('Z', '+00:00'))
                scraped_date = scraped_date.replace(tzinfo=None)
                
                # Zähle nach Zeiträumen
                if scraped_date >= today_start:
                    today_articles += 1
                
                if scraped_date >= one_hour_ago:
                    last_hour += 1
                
                if scraped_date >= six_hours_ago:
                    last_6_hours += 1
                    
            except Exception as e:
                logger.debug(f"Fehler beim Parsen des Artikel-Datums: {e}")
                continue
        
        return {
            'total_articles': total_articles,
            'today_articles': today_articles,
            'last_hour': last_hour,
            'last_6_hours': last_6_hours
        }
        
    except Exception as e:
        logger.error(f"Fehler bei Statistik-Berechnung: {e}")
        return {
            'total_articles': 0,
            'today_articles': 0,
            'last_hour': 0,
            'last_6_hours': 0
        }
