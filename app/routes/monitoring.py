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
    """Extrahiert relevante Logs aus Docker-Container"""
    import subprocess
    
    logs = []
    containers = ['ticker_celery', 'ticker_celery_beat', 'ticker_webapp']
    
    for container in containers:
        try:
            # Docker-Logs abrufen
            cmd = ['sudo', 'docker', 'logs', container, '--tail', str(lines), '--timestamps']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                log_lines = result.stdout.split('\n')
                
                for line in log_lines:
                    if not line.strip():
                        continue
                    
                    parsed_log = _parse_log_line(line, container)
                    if parsed_log:
                        # Filter anwenden
                        if level_filter and parsed_log.get('level') != level_filter:
                            continue
                        if source_filter and source_filter.lower() not in parsed_log.get('message', '').lower():
                            continue
                        
                        logs.append(parsed_log)
        
        except Exception as e:
            logger.warning(f"Fehler beim Laden der Logs von {container}: {e}")
    
    # Nach Timestamp sortieren (neueste zuerst)
    logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    return logs[:lines]


def _parse_log_line(line, container):
    """Parsed eine Docker-Log-Zeile"""
    try:
        # Format: 2025-08-09T20:30:00.012345Z [2025-08-09 20:30:00,012: INFO/MainProcess] Message
        
        # Docker-Timestamp extrahieren
        timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\s+(.*)$', line)
        if not timestamp_match:
            return None
        
        docker_timestamp, log_content = timestamp_match.groups()
        
        # Log-Level und Message extrahieren
        level_match = re.search(r'\[(.*?): (INFO|WARNING|ERROR|DEBUG)/.*?\] (.*)', log_content)
        if level_match:
            celery_timestamp, level, message = level_match.groups()
            
            return {
                'timestamp': docker_timestamp,
                'level': level,
                'message': message.strip(),
                'container': container,
                'source': _determine_source(message)
            }
        
        # Fallback für einfache Nachrichten
        return {
            'timestamp': docker_timestamp,
            'level': 'INFO',
            'message': log_content.strip(),
            'container': container,
            'source': 'system'
        }
        
    except Exception as e:
        logger.debug(f"Fehler beim Parsen der Log-Zeile: {e}")
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
