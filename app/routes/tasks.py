"""
Tasks Routes für manuelle Task-Ausführung
"""

from flask import Blueprint, jsonify, request
from app.tasks.scraping_tasks import monitor_telegram_task, monitor_telethon_task, cleanup_old_articles_task, health_check
import logging

bp = Blueprint('tasks', __name__, url_prefix='/tasks')
logger = logging.getLogger(__name__)


@bp.route('/telegram/start', methods=['POST'])
def start_telegram_monitoring():
    """Startet manuell das Telegram-Monitoring (Bot API)"""
    try:
        # Task asynchron starten
        task = monitor_telegram_task.delay()
        
        return jsonify({
            'success': True,
            'message': 'Telegram-Monitoring gestartet (Bot API)',
            'task_id': task.id,
            'status': 'started',
            'scraper': 'bot_api'
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Starten des Telegram-Monitorings: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Fehler beim Starten des Telegram-Monitorings'
        }), 500


@bp.route('/telethon/start', methods=['POST'])
def start_telethon_monitoring():
    """Startet manuell das Telethon-Monitoring"""
    try:
        # Task asynchron starten
        task = monitor_telethon_task.delay()
        
        return jsonify({
            'success': True,
            'message': 'Telethon-Monitoring gestartet',
            'task_id': task.id,
            'status': 'started',
            'scraper': 'telethon'
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Starten des Telethon-Monitorings: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Fehler beim Starten des Telethon-Monitorings'
        }), 500


@bp.route('/cleanup/start', methods=['POST'])
def start_cleanup():
    """Startet manuell das Cleanup alter Artikel"""
    try:
        # Task asynchron starten
        task = cleanup_old_articles_task.delay()
        
        return jsonify({
            'success': True,
            'message': 'Artikel-Cleanup gestartet',
            'task_id': task.id,
            'status': 'started'
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Starten des Cleanups: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Fehler beim Starten des Cleanups'
        }), 500


@bp.route('/health', methods=['GET'])
def health_check_route():
    """Führt einen Health-Check aus"""
    try:
        # Task synchron ausführen
        result = health_check.delay()
        
        # Kurz warten auf Ergebnis
        try:
            health_status = result.get(timeout=5)
            return jsonify({
                'success': True,
                'health_status': health_status,
                'task_id': result.id
            })
        except Exception:
            return jsonify({
                'success': True,
                'message': 'Health-Check gestartet (async)',
                'task_id': result.id,
                'status': 'started'
            })
        
    except Exception as e:
        logger.error(f"Fehler beim Health-Check: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Fehler beim Health-Check'
        }), 500


@bp.route('/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Überprüft den Status einer Task"""
    try:
        from app.celery_app import celery_app
        
        result = celery_app.AsyncResult(task_id)
        
        status_info = {
            'task_id': task_id,
            'status': result.status,
            'ready': result.ready(),
            'successful': result.successful() if result.ready() else None
        }
        
        if result.ready():
            if result.successful():
                status_info['result'] = result.result
            else:
                status_info['error'] = str(result.result)
        
        return jsonify({
            'success': True,
            'task_status': status_info
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Task-Status: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Fehler beim Abrufen des Task-Status'
        }), 500


@bp.route('/list', methods=['GET'])
def list_active_tasks():
    """Listet alle aktiven Tasks auf"""
    try:
        from app.celery_app import celery_app
        
        # Aktive Tasks abrufen
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        
        return jsonify({
            'success': True,
            'active_tasks': active_tasks or {},
            'message': f'Aktive Tasks abgerufen'
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen aktiver Tasks: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Fehler beim Abrufen aktiver Tasks'
        }), 500
