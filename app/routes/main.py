"""
Main Routes - Dashboard und Homepage
"""

from flask import Blueprint, render_template, jsonify
from app.data import json_manager
import logging

bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)


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
