"""
Housekeeping Routes für Datenbereinigung
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from datetime import datetime
import logging

from app.tasks.housekeeping_tasks import (
    HousekeepingManager,
    cleanup_old_articles_task,
    cleanup_orphaned_media_task,
    cleanup_old_backups_task,
    full_cleanup_task,
    get_storage_stats_task
)
from config.config import Config

# Setup logging
logger = logging.getLogger(__name__)

# Blueprint erstellen
housekeeping_bp = Blueprint('housekeeping', __name__, url_prefix='/housekeeping')


@housekeeping_bp.route('/')
def dashboard():
    """Housekeeping Dashboard anzeigen"""
    try:
        # Aktuelle Speicher-Statistiken laden
        manager = HousekeepingManager()
        storage_stats = manager.get_storage_stats()
        
        # Konfigurationswerte
        config_info = {
            'cleanup_days': Config.CLEANUP_DAYS,
            'backup_retention_days': Config.BACKUP_RETENTION_DAYS,
            'auto_backup': Config.AUTO_BACKUP,
            'housekeeping_enabled': Config.HOUSEKEEPING_ENABLED,
            'auto_cleanup_articles': Config.AUTO_CLEANUP_ARTICLES,
            'auto_cleanup_media': Config.AUTO_CLEANUP_MEDIA
        }
        
        return render_template(
            'housekeeping/dashboard.html',
            storage_stats=storage_stats,
            config=config_info,
            current_time=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Fehler beim Laden des Housekeeping-Dashboards: {e}")
        flash(f'Fehler beim Laden der Statistiken: {str(e)}', 'error')
        return render_template('housekeeping/dashboard.html', 
                             storage_stats=None, 
                             config={},
                             current_time=datetime.now())


@housekeeping_bp.route('/api/storage-stats')
def api_storage_stats():
    """API: Aktuelle Speicher-Statistiken"""
    try:
        # Async Task für bessere Performance
        task = get_storage_stats_task.delay()
        stats = task.get(timeout=30)
        
        return jsonify({
            'success': True,
            'data': stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Laden der Speicher-Statistiken: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@housekeeping_bp.route('/cleanup/articles', methods=['POST'])
def cleanup_articles():
    """Artikel bereinigen"""
    try:
        # Optional: Anzahl Tage aus Form
        days = request.form.get('days', type=int)
        
        # Direkter Aufruf des Managers
        manager = HousekeepingManager()
        result = manager.cleanup_old_articles(days)
        
        flash(f'✅ Artikel-Bereinigung abgeschlossen: {result["removed_count"]} Artikel entfernt', 'success')
        
        return jsonify({
            'success': True,
            'message': f'{result["removed_count"]} Artikel entfernt',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Fehler bei Artikel-Bereinigung: {e}")
        error_msg = f'Fehler bei Artikel-Bereinigung: {str(e)}'
        flash(error_msg, 'error')
        
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500


@housekeeping_bp.route('/cleanup/media', methods=['POST'])
def cleanup_media():
    """Verwaiste Media-Files bereinigen"""
    try:
        # Direkter Aufruf des Managers
        manager = HousekeepingManager()
        result = manager.cleanup_orphaned_media()
        
        flash(f'✅ Media-Bereinigung abgeschlossen: {result["removed_count"]} Dateien entfernt', 'success')
        
        return jsonify({
            'success': True,
            'message': f'{result["removed_count"]} Dateien entfernt',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Fehler bei Media-Bereinigung: {e}")
        error_msg = f'Fehler bei Media-Bereinigung: {str(e)}'
        flash(error_msg, 'error')
        
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500


@housekeeping_bp.route('/cleanup/backups', methods=['POST'])
def cleanup_backups():
    """Alte Backups bereinigen"""
    try:
        # Optional: Anzahl Tage aus Form
        days = request.form.get('days', type=int)
        
        # Direkter Aufruf des Managers
        manager = HousekeepingManager()
        result = manager.cleanup_old_backups(days)
        
        flash(f'✅ Backup-Bereinigung abgeschlossen: {result["removed_count"]} Backups entfernt', 'success')
        
        return jsonify({
            'success': True,
            'message': f'{result["removed_count"]} Backups entfernt',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Fehler bei Backup-Bereinigung: {e}")
        error_msg = f'Fehler bei Backup-Bereinigung: {str(e)}'
        flash(error_msg, 'error')
        
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500


@housekeeping_bp.route('/toggle-auto-cleanup', methods=['POST'])
def toggle_auto_cleanup():
    """Toggle automatische Bereinigung"""
    try:
        # TODO: Hier würde normalerweise die Konfiguration in der Datenbank/Datei gespeichert
        # Für jetzt nur eine Bestätigung zurückgeben
        enabled = request.json.get('enabled', False)
        
        # In einer echten Implementierung würde hier die Konfiguration gespeichert werden
        # config_manager.update_setting('auto_cleanup_enabled', enabled)
        
        message = 'Automatische Bereinigung aktiviert' if enabled else 'Automatische Bereinigung deaktiviert'
        flash(f'✅ {message}', 'success')
        
        return jsonify({
            'success': True,
            'message': message,
            'enabled': enabled
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Toggle der automatischen Bereinigung: {e}")
        error_msg = f'Fehler: {str(e)}'
        flash(error_msg, 'error')
        
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500


@housekeeping_bp.route('/cleanup/full', methods=['POST'])
def full_cleanup():
    """Vollständige Bereinigung durchführen"""
    try:
        # Direkter Aufruf des Managers
        manager = HousekeepingManager()
        
        # Alle Bereinigungsaktionen durchführen
        article_result = manager.cleanup_old_articles()
        media_result = manager.cleanup_orphaned_media()
        backup_result = manager.cleanup_old_backups()
        
        total_removed = (
            article_result.get('removed_count', 0) +
            media_result.get('removed_count', 0) +
            backup_result.get('removed_count', 0)
        )
        
        flash(f'✅ Vollständige Bereinigung abgeschlossen: {total_removed} Elemente entfernt', 'success')
        
        return jsonify({
            'success': True,
            'message': f'Vollständige Bereinigung abgeschlossen: {total_removed} Elemente entfernt',
            'data': {
                'articles': article_result,
                'media': media_result,
                'backups': backup_result,
                'total_removed': total_removed
            }
        })
        
    except Exception as e:
        logger.error(f"Fehler bei vollständiger Bereinigung: {e}")
        error_msg = f'Fehler bei vollständiger Bereinigung: {str(e)}'
        flash(error_msg, 'error')
        
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500
