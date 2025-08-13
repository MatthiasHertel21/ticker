"""
Housekeeping Routes für Datenbereinigung und Spam-Verwaltung
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from datetime import datetime
import logging

from app.utils.timezone_utils import get_cet_time
from app.utils.spam_detector import spam_detector
from app.data import json_manager

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
            'cleanup_days': getattr(Config, 'CLEANUP_DAYS', 3),
            'backup_retention_days': getattr(Config, 'BACKUP_RETENTION_DAYS', 7),
            'auto_backup': getattr(Config, 'AUTO_BACKUP', True),
            'housekeeping_enabled': getattr(Config, 'HOUSEKEEPING_ENABLED', True),
            'auto_cleanup_articles': getattr(Config, 'AUTO_CLEANUP_ARTICLES', True),
            'auto_cleanup_media': getattr(Config, 'AUTO_CLEANUP_MEDIA', True),
            'spam_detection_enabled': getattr(Config, 'SPAM_DETECTION_ENABLED', True),
            'spam_threshold': getattr(Config, 'SPAM_THRESHOLD', 0.7),
            'spam_auto_mark': getattr(Config, 'SPAM_AUTO_MARK', True)
        }
        
        return render_template(
            'housekeeping/dashboard.html',
            storage_stats=storage_stats,
            config=config_info,
            current_time=get_cet_time()
        )
        
    except Exception as e:
        logger.error(f"Fehler beim Laden des Housekeeping-Dashboards: {e}")
        flash(f'Fehler beim Laden der Statistiken: {str(e)}', 'error')
        return render_template('housekeeping/dashboard.html', 
                             storage_stats=None, 
                             config={},
                             current_time=get_cet_time())


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
            'timestamp': get_cet_time().isoformat()
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
        

@housekeeping_bp.route('/spam')
def spam_management():
    """Spam-Verwaltung Dashboard anzeigen"""
    try:
        # Lade alle Artikel
        articles_data = json_manager.read('articles')
        articles = articles_data.get('articles', []) if articles_data else []
        
        # Filtere Spam-Artikel
        spam_articles = [a for a in articles if a.get('relevance_score') == 'spam']
        suspected_spam = [a for a in articles if a.get('spam_detection', {}).get('spam_score', 0) > 0.5 and a.get('relevance_score') != 'spam']
        
        # Spam-Statistiken
        spam_stats = {
            'total_articles': len(articles),
            'spam_articles': len(spam_articles),
            'suspected_spam': len(suspected_spam),
            'spam_percentage': (len(spam_articles) / len(articles) * 100) if articles else 0
        }
        
        return render_template(
            'housekeeping/spam_management.html',
            spam_articles=spam_articles[:50],  # Zeige nur die ersten 50
            suspected_spam=suspected_spam[:50],
            spam_stats=spam_stats,
            current_time=get_cet_time()
        )
        
    except Exception as e:
        logger.error(f"Fehler beim Laden der Spam-Verwaltung: {e}")
        flash(f'Fehler beim Laden der Spam-Verwaltung: {str(e)}', 'error')
        return redirect(url_for('housekeeping.dashboard'))


@housekeeping_bp.route('/spam/mark/<article_id>', methods=['POST'])
def mark_spam(article_id):
    """Markiert einen Artikel als Spam"""
    try:
        articles_data = json_manager.read('articles')
        articles = articles_data.get('articles', []) if articles_data else []
        
        # Finde den Artikel
        for article in articles:
            if article.get('id') == article_id:
                article['relevance_score'] = 'spam'
                article['spam_manually_marked'] = True
                article['spam_marked_at'] = datetime.now().isoformat()
                break
        
        # Speichere die Änderungen
        json_manager.write('articles', {'articles': articles})
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Fehler beim Markieren als Spam: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@housekeeping_bp.route('/spam/unmark/<article_id>', methods=['POST'])
def unmark_spam(article_id):
    """Entfernt Spam-Markierung von einem Artikel"""
    try:
        articles_data = json_manager.read('articles')
        articles = articles_data.get('articles', []) if articles_data else []
        
        # Finde den Artikel
        for article in articles:
            if article.get('id') == article_id:
                # Setze auf Default-Score zurück
                article['relevance_score'] = 'unread'
                if 'spam_manually_marked' in article:
                    del article['spam_manually_marked']
                if 'spam_marked_at' in article:
                    del article['spam_marked_at']
                break
        
        # Speichere die Änderungen
        json_manager.write('articles', {'articles': articles})
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Fehler beim Entfernen der Spam-Markierung: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@housekeeping_bp.route('/spam/cleanup', methods=['POST'])
def cleanup_spam():
    """Entfernt alle als Spam markierten Artikel endgültig"""
    try:
        articles_data = json_manager.read('articles')
        articles = articles_data.get('articles', []) if articles_data else []
        
        # Zähle Spam-Artikel vor der Bereinigung
        spam_count = len([a for a in articles if a.get('relevance_score') == 'spam'])
        
        # Entferne alle Spam-Artikel
        cleaned_articles = [a for a in articles if a.get('relevance_score') != 'spam']
        
        # Speichere die bereinigten Artikel
        json_manager.write('articles', {'articles': cleaned_articles})
        
        flash(f'{spam_count} Spam-Artikel erfolgreich entfernt', 'success')
        return jsonify({'success': True, 'removed_count': spam_count})
        
    except Exception as e:
        logger.error(f"Fehler bei Spam-Bereinigung: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500
