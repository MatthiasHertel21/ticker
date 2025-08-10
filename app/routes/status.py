"""
System-Status für Telethon-Session
"""

from flask import Blueprint, jsonify
from app.data import json_manager
import os
import logging

bp = Blueprint('status', __name__, url_prefix='/api/status')
logger = logging.getLogger(__name__)


@bp.route('/telethon')
def telethon_status():
    """Prüft den Telethon-Session-Status"""
    try:
        # Prüfe Session-File
        session_path = '/app/data/telethon_session.session'
        session_exists = os.path.exists(session_path)
        
        # Prüfe API-Konfiguration
        api_id = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        api_configured = bool(api_id and api_hash)
        
        # Versuche Telethon-Client zu testen
        client_ready = False
        error_message = None
        
        if session_exists and api_configured:
            try:
                from app.scrapers.telethon_scraper import sync_check_telethon_ready
                client_ready = sync_check_telethon_ready()
            except Exception as e:
                error_message = str(e)
                logger.error(f"Telethon-Status-Check fehlgeschlagen: {e}")
        
        status = {
            'session_exists': session_exists,
            'api_configured': api_configured,
            'client_ready': client_ready,
            'error_message': error_message,
            'session_path': session_path,
            'status': 'ready' if (session_exists and api_configured and client_ready) else 'error'
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Fehler beim Telethon-Status-Check: {e}")
        return jsonify({
            'status': 'error',
            'error_message': str(e),
            'session_exists': False,
            'api_configured': False,
            'client_ready': False
        }), 500


@bp.route('/system')
def system_status():
    """Allgemeiner System-Status"""
    try:
        # Prüfe Datenbank-Zugriff
        articles = json_manager.read('articles')
        sources = json_manager.read('sources')
        
        # Berechne Statistiken
        article_count = len(articles.get('articles', []))
        source_count = len(sources.get('sources', {}))
        
        # Prüfe Container-Status (vereinfacht)
        import subprocess
        try:
            result = subprocess.run(['sudo', 'docker', 'ps', '--format', 'json'], 
                                 capture_output=True, text=True, timeout=5)
            containers_running = len(result.stdout.strip().split('\n')) if result.returncode == 0 else 0
        except:
            containers_running = 0
        
        status = {
            'status': 'healthy',
            'components': {
                'json_storage': True,
                'data_access': True,
                'containers': containers_running > 0
            },
            'statistics': {
                'articles': article_count,
                'sources': source_count,
                'containers': containers_running
            }
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"System-Status-Check fehlgeschlagen: {e}")
        return jsonify({
            'status': 'error',
            'error_message': str(e),
            'components': {
                'json_storage': False,
                'data_access': False,
                'containers': False
            }
        }), 500
