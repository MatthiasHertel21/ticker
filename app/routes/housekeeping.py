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
    """Housekeeping Dashboard"""
    try:
        # Aktuelle Speicher-Statistiken laden
        manager = HousekeepingManager()
        storage_stats = manager.get_storage_stats()
        
        # Konfigurationswerte
        config_info = {
            'cleanup_days': Config.CLEANUP_DAYS,
            'backup_retention_days': Config.BACKUP_RETENTION_DAYS,
            'auto_backup': Config.AUTO_BACKUP
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
                             config={})


@housekeeping_bp.route('/api/storage-stats')
def api_storage_stats():
    """API: Aktuelle Speicher-Statistiken"""
    try:
        # Async Task für bessere Performance
        task = get_storage_stats_task.delay()
        stats = task.get(timeout=30)
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Speicher-Statistiken: {e}")
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
        
        # Async Task starten
        task = cleanup_old_articles_task.delay(days)
        result = task.get(timeout=120)  # 2 Minuten Timeout
        
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
        # Async Task starten
        task = cleanup_orphaned_media_task.delay()
        result = task.get(timeout=60)
        
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
        
        # Async Task starten
        task = cleanup_old_backups_task.delay(days)
        result = task.get(timeout=60)
        
        flash(f'✅ Backup-Bereinigung abgeschlossen: {result["removed_count"]} Backups entfernt ({result["size_freed_mb"]} MB)', 'success')
        
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


@housekeeping_bp.route('/cleanup/full', methods=['POST'])
def full_cleanup():
    """Vollständige Bereinigung"""
    try:
        # Async Task starten (längerer Timeout für vollständige Bereinigung)
        task = full_cleanup_task.delay()
        result = task.get(timeout=300)  # 5 Minuten Timeout
        
        total_articles = result['articles_cleanup']['removed_count']
        total_media = result['orphaned_media_cleanup']['removed_count']
        total_backups = result['backup_cleanup']['removed_count']
        total_saved = result['storage_saved_mb']
        
        flash(f'✅ Vollständige Bereinigung abgeschlossen: {total_articles} Artikel, {total_media} Media-Files, {total_backups} Backups entfernt ({total_saved} MB)', 'success')
        
        return jsonify({
            'success': True,
            'message': f'Bereinigung abgeschlossen: {total_saved} MB freigegeben',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Fehler bei vollständiger Bereinigung: {e}")
        error_msg = f'Fehler bei vollständiger Bereinigung: {str(e)}'
        flash(error_msg, 'error')
        
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500


@housekeeping_bp.route('/config', methods=['GET', 'POST'])
def config_page():
    """Housekeeping-Konfiguration"""
    if request.method == 'POST':
        try:
            # Hier könnte man dynamische Konfiguration implementieren
            # Für jetzt nur Info zurückgeben
            flash('ℹ️ Konfiguration wird über Umgebungsvariablen verwaltet', 'info')
            
        except Exception as e:
            logger.error(f"Fehler bei Konfiguration: {e}")
            flash(f'Fehler bei Konfiguration: {str(e)}', 'error')
    
    config_info = {
        'cleanup_days': Config.CLEANUP_DAYS,
        'backup_retention_days': Config.BACKUP_RETENTION_DAYS,
        'auto_backup': Config.AUTO_BACKUP,
        'max_articles_per_source': Config.MAX_ARTICLES_PER_SOURCE
    }
    
    return render_template('housekeeping/config.html', config=config_info)


# JavaScript Helper für AJAX-Requests
@housekeeping_bp.route('/js/housekeeping.js')
def housekeeping_js():
    """JavaScript für Housekeeping-UI"""
    js_content = '''
// Housekeeping JavaScript Functions
class HousekeepingManager {
    constructor() {
        this.initEventListeners();
        this.refreshInterval = null;
    }
    
    initEventListeners() {
        // Auto-refresh Storage Stats
        document.addEventListener('DOMContentLoaded', () => {
            this.refreshStorageStats();
            this.startAutoRefresh();
        });
        
        // Cleanup Buttons
        document.querySelectorAll('[data-cleanup-action]').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleCleanupAction(button);
            });
        });
    }
    
    async handleCleanupAction(button) {
        const action = button.dataset.cleanupAction;
        const form = button.closest('form');
        
        // Button deaktivieren
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Bereinige...';
        
        try {
            const formData = new FormData(form);
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showMessage(result.message, 'success');
                this.refreshStorageStats();
            } else {
                this.showMessage(result.error || 'Unbekannter Fehler', 'error');
            }
            
        } catch (error) {
            this.showMessage('Netzwerkfehler: ' + error.message, 'error');
        } finally {
            // Button zurücksetzen
            button.disabled = false;
            button.innerHTML = button.dataset.originalText || 'Bereinigen';
        }
    }
    
    async refreshStorageStats() {
        try {
            const response = await fetch('/housekeeping/api/storage-stats');
            const result = await response.json();
            
            if (result.success) {
                this.updateStorageDisplay(result.data);
            }
        } catch (error) {
            console.error('Fehler beim Aktualisieren der Speicher-Statistiken:', error);
        }
    }
    
    updateStorageDisplay(stats) {
        // Update verschiedene Statistik-Elemente
        const elements = {
            'articles-count': stats.articles.count,
            'articles-size': stats.articles.size_mb + ' MB',
            'media-count': stats.media.count,
            'media-size': stats.media.size_mb + ' MB',
            'backups-count': stats.backups.count,
            'backups-size': stats.backups.size_mb + ' MB',
            'total-size': stats.total.size_mb + ' MB'
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
        
        // Update Timestamp
        const timestampElement = document.getElementById('stats-timestamp');
        if (timestampElement) {
            timestampElement.textContent = new Date().toLocaleString();
        }
    }
    
    showMessage(message, type) {
        // Erstelle Bootstrap Alert
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Füge zum Container hinzu
        const container = document.querySelector('.alert-container') || document.querySelector('.container');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
        }
        
        // Auto-remove nach 5 Sekunden
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
    
    startAutoRefresh() {
        // Refresh alle 30 Sekunden
        this.refreshInterval = setInterval(() => {
            this.refreshStorageStats();
        }, 30000);
    }
    
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
}

// Initialize
const housekeepingManager = new HousekeepingManager();
'''
    
    from flask import Response
    return Response(js_content, mimetype='application/javascript')
