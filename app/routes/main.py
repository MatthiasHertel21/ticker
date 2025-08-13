"""
Main Routes - Dashboard und Homepage
"""

from flask import Blueprint, render_template, jsonify, request
from app.data import json_manager
import logging
import json
import os
from datetime import datetime

bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)


# TEMPORÄRE TOGGLE ROUTE - bis die Sources-Route wieder funktioniert
@bp.route('/sources/toggle-status', methods=['POST'])
def toggle_source_status():
    """Status einer Quelle umschalten (aktiv/inaktiv)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Keine JSON-Daten empfangen'}), 400
            
        source_identifier = data.get('source_name')
        new_status = data.get('enabled')
        
        if not source_identifier:
            return jsonify({'error': 'Quellenidentifier erforderlich'}), 400
        
        if new_status is None:
            return jsonify({'error': 'Status erforderlich'}), 400
        
        logger.info(f"Toggle request for source: {source_identifier}, status: {new_status}")
        
        # Direkter Zugriff auf JSON-Datei
        sources_file = '/home/ga/ticker/data/sources.json'
        
        if not os.path.exists(sources_file):
            return jsonify({'error': 'Sources-Datei nicht gefunden'}), 404
        
        # JSON-Datei lesen
        with open(sources_file, 'r', encoding='utf-8') as f:
            sources_data = json.load(f)
        
        # Prüfen ob neue Struktur (mit sources Array) oder alte Struktur
        if isinstance(sources_data, dict) and 'sources' in sources_data:
            sources = sources_data['sources']
        else:
            sources = sources_data if isinstance(sources_data, list) else []
        
        # Quelle finden und Status ändern
        source_found = False
        source_name = source_identifier
        
        for source in sources:
            # Prüfen auf verschiedene Identifier (ID, Name, source_name)
            if (source.get('id') == source_identifier or 
                source.get('name') == source_identifier or 
                source.get('source_name') == source_identifier):
                
                source['enabled'] = bool(new_status)
                source['updated_at'] = datetime.now().isoformat()
                source_found = True
                source_name = source.get('name', source.get('source_name', source_identifier))
                logger.info(f"Found and updated source: {source_name}")
                break
        
        if not source_found:
            logger.warning(f"Source not found: {source_identifier}")
            return jsonify({'error': f'Quelle "{source_identifier}" nicht gefunden'}), 404
        
        # Änderungen speichern
        with open(sources_file, 'w', encoding='utf-8') as f:
            json.dump(sources_data, f, indent=2, ensure_ascii=False)
        
        # Erfolgsmeldung
        status_text = "aktiviert" if new_status else "deaktiviert"
        message = f"Quelle '{source_name}' wurde {status_text}"
        
        logger.info(f"Source status geändert: {source_identifier} -> {status_text}")
        
        return jsonify({
            'success': True,
            'message': message,
            'source_name': source_name,
            'enabled': bool(new_status)
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Umschalten des Quellenstatus: {e}", exc_info=True)
        return jsonify({'error': f'Fehler beim Ändern des Status: {str(e)}'}), 500


@bp.route('/')
def index():
    """Homepage mit Artikelübersicht statt Dashboard"""
    try:
        # Redirect zur Artikelseite
        from flask import redirect, url_for
        return redirect(url_for('articles.articles_dashboard'))
    except Exception as e:
        logger.error(f"Fehler beim Weiterleiten zur Artikelseite: {e}")
        # Fallback zum alten Dashboard
        return dashboard()


@bp.route('/dashboard')
def dashboard():
    """Dashboard-Übersicht (ehemals Homepage)"""
    try:
        # Statistiken laden
        articles = json_manager.read('articles')
        sources = json_manager.read('sources')
        
        # Artikel-Statistiken berechnen
        articles_data = articles.get('articles', [])
        if isinstance(articles_data, list):
            total_articles = len(articles_data)
        else:
            total_articles = len(articles_data)
        
        # Telegram-Quellen zählen
        telegram_sources = sources.get('telegram', {})
        total_telegram_channels = len(telegram_sources)
        
        # Dashboard-Daten zusammenstellen
        dashboard_stats = {
            'total_articles': total_articles,
            'total_sources': total_telegram_channels,
            'total_telegram_channels': total_telegram_channels,
            'system_status': 'active'
        }
        
        # Neueste Artikel für Vorschau
        recent_articles = []
        articles_data = articles.get('articles', [])
        
        # Wenn articles_data eine Liste ist (neue Struktur)
        if isinstance(articles_data, list):
            # Sortiere nach Datum (neueste zuerst)
            sorted_articles = sorted(
                articles_data,
                key=lambda x: x.get('published_date', x.get('published_at', '')),
                reverse=True
            )[:5]  # Top 5 neueste Artikel
            
            for article_data in sorted_articles:
                recent_articles.append({
                    'id': article_data.get('id', ''),
                    'title': article_data.get('title', 'Unbekannter Titel'),
                    'source': article_data.get('source', 'Unbekannte Quelle'),
                    'published_at': article_data.get('published_date', article_data.get('published_at', '')),
                    'keywords': article_data.get('keywords', [])[:3] if article_data.get('keywords') else []
                })
        else:
            # Alte Dictionary-Struktur (Fallback)
            sorted_articles = sorted(
                articles_data.items(),
                key=lambda x: x[1].get('published_at', ''),
                reverse=True
            )[:5]
            
            for article_id, article_data in sorted_articles:
                recent_articles.append({
                    'id': article_id,
                    'title': article_data.get('title', 'Unbekannter Titel'),
                    'source': article_data.get('source', 'Unbekannte Quelle'),
                    'published_at': article_data.get('published_at', ''),
                    'keywords': article_data.get('keywords', [])[:3] if article_data.get('keywords') else []
                })
        
        return render_template('dashboard.html', 
                             stats=dashboard_stats, 
                             recent_articles=recent_articles)
        
    except Exception as e:
        logger.error(f"Fehler beim Laden der Dashboard-Daten: {e}")
        # Fallback-Dashboard
        return render_template('dashboard.html', 
                             stats={'total_articles': 0, 'total_sources': 0, 'system_status': 'error'},
                             recent_articles=[])


@bp.route('/health')
def health_check():
    """System Health Check"""
    try:
        # Teste JSON-Datenzugriff
        sources = json_manager.read('sources')
        articles = json_manager.read('articles')
        
        health_status = {
            'status': 'healthy',
            'timestamp': None,
            'components': {
                'json_storage': True,
                'data_access': True,
                'sources_count': len(sources.get('telegram', {})),
                'articles_count': len(articles.get('articles', [])) if isinstance(articles.get('articles', []), list) else len(articles.get('articles', {}))
            }
        }
        
        return jsonify(health_status), 200
        
    except Exception as e:
        logger.error(f"Health Check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503


@bp.route('/api/stats')
def api_stats():
    """API-Endpunkt für Dashboard-Statistiken"""
    try:
        articles = json_manager.read('articles')
        sources = json_manager.read('sources')
        
        articles_data = articles.get('articles', [])
        articles_count = len(articles_data) if isinstance(articles_data, list) else len(articles_data)
        
        stats = {
            'articles': {
                'total': articles_count,
                'today': 0,  # TODO: Implementiere Tages-Filter
                'this_week': 0  # TODO: Implementiere Wochen-Filter
            },
            'sources': {
                'telegram': len(sources.get('telegram', {})),
                'total': len(sources.get('telegram', {}))
            },
            'system': {
                'status': 'active',
                'last_update': articles.get('metadata', {}).get('last_updated', 'Unknown')
            }
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Fehler beim Laden der API-Statistiken: {e}")
        return jsonify({'error': str(e)}), 500
