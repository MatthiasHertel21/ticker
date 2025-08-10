"""
Article Management Routes
"""

from flask import Blueprint, request, jsonify, render_template
from app.data import json_manager
import datetime
import logging

bp = Blueprint('articles', __name__, url_prefix='/articles')
logger = logging.getLogger(__name__)


@bp.route('/')
def articles_dashboard():
    """Artikel-Dashboard mit Bootstrap 5 Design"""
    articles = json_manager.read('articles')
    
    # Hole Artikel-Liste (unterstützt sowohl neue Liste als auch alte Dictionary-Struktur)
    articles_data = articles.get('articles', [])
    
    if isinstance(articles_data, list):
        # Neue Struktur: bereits eine Liste
        article_list = articles_data
    else:
        # Alte Struktur: Dictionary mit values()
        article_list = list(articles_data.values())
    
    # Sortiere nach Datum (neueste zuerst) - unterstützt beide Datumsfelder
    article_list.sort(key=lambda x: x.get('published_date', x.get('published_at', '')), reverse=True)
    
    # Filtere Spam-Artikel aus der Anzeige heraus
    article_list = [article for article in article_list if article.get('relevance_score') != 'spam']
    
    # Hole Page-Parameter für Paginierung
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)  # Standard: 100 pro Seite
    
    # Berechne Start- und End-Index
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    # Paginierte Artikel
    paginated_articles = article_list[start_idx:end_idx]
    total_articles = len(article_list)
    has_more = end_idx < total_articles
    
    return render_template('articles.html', 
                         articles=paginated_articles,
                         page=page,
                         per_page=per_page,
                         total_articles=total_articles,
                         has_more=has_more)


@bp.route('/rate/<article_id>', methods=['POST'])
def rate_article(article_id):
    """Bewerte einen Artikel"""
    try:
        data = request.get_json()
        rating = data.get('rating')
        
        if rating not in ['favorite', 'spam', 'high', 'medium', 'low']:  # Unterstütze alte und neue Werte
            return jsonify({'success': False, 'error': 'Ungültiges Rating'})
        
        # Artikel laden und bewerten
        articles = json_manager.read('articles')
        articles_data = articles.get('articles', [])
        
        # Finde den Artikel in der Liste
        article_found = False
        for article in articles_data:
            if article.get('id') == article_id:
                article['relevance_score'] = rating
                article['rated_at'] = datetime.datetime.now().isoformat()
                article_found = True
                break
        
        if not article_found:
            return jsonify({'success': False, 'error': 'Artikel nicht gefunden'})
        
        # Speichere die aktualisierte Liste
        articles['articles'] = articles_data
        json_manager.write('articles', articles)
        
        return jsonify({
            'success': True,
            'message': f'Artikel als {rating} bewertet'
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Bewerten von Artikel {article_id}: {e}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/mark-twitter/<article_id>', methods=['POST'])
def mark_for_twitter(article_id):
    """Markiere einen Artikel für Twitter"""
    try:
        articles = json_manager.read('articles')
        articles_data = articles.get('articles', [])
        
        # Finde den Artikel in der Liste
        article_found = False
        for article in articles_data:
            if article.get('id') == article_id:
                article['is_used_for_twitter'] = True
                article['marked_for_twitter_at'] = datetime.datetime.now().isoformat()
                article_found = True
                break
        
        if not article_found:
            return jsonify({'success': False, 'error': 'Artikel nicht gefunden'})
        
        # Speichere die aktualisierte Liste
        articles['articles'] = articles_data
        json_manager.write('articles', articles)
        
        return jsonify({
            'success': True,
            'message': 'Artikel für Twitter markiert'
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Twitter-Markieren von Artikel {article_id}: {e}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/delete/<article_id>', methods=['POST'])
def delete_article(article_id):
    """Lösche einen Artikel"""
    try:
        articles = json_manager.read('articles')
        articles_data = articles.get('articles', [])
        
        # Finde und entferne den Artikel aus der Liste
        article_found = False
        for i, article in enumerate(articles_data):
            if article.get('id') == article_id:
                articles_data.pop(i)
                article_found = True
                break
        
        if not article_found:
            return jsonify({'success': False, 'error': 'Artikel nicht gefunden'})
        
        # Speichere die aktualisierte Liste
        articles['articles'] = articles_data
        json_manager.write('articles', articles)
        
        return jsonify({'success': True, 'message': 'Artikel gelöscht'})
    except Exception as e:
        logger.error(f"Fehler beim Löschen von Artikel {article_id}: {e}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/bulk-action', methods=['POST'])
def bulk_action():
    """Bulk-Aktionen für mehrere Artikel"""
    try:
        data = request.get_json()
        action = data.get('action')
        article_ids = data.get('article_ids', [])
        
        if not article_ids:
            return jsonify({'success': False, 'error': 'Keine Artikel ausgewählt'})
        
        articles = json_manager.read('articles')
        
        if action == 'delete':
            for article_id in article_ids:
                if article_id in articles.get('articles', {}):
                    del articles['articles'][article_id]
        
        elif action == 'mark_twitter':
            for article_id in article_ids:
                if article_id in articles.get('articles', {}):
                    articles['articles'][article_id]['is_used_for_twitter'] = True
                    articles['articles'][article_id]['marked_for_twitter_at'] = datetime.datetime.now().isoformat()
        
        json_manager.write('articles', articles)
        
        return jsonify({
            'success': True,
            'message': f'{action} für {len(article_ids)} Artikel ausgeführt'
        })
        
    except Exception as e:
        logger.error(f"Bulk-Aktion fehlgeschlagen: {e}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/<article_id>/preview')
def get_article_preview(article_id):
    """Get link previews for an article asynchronously"""
    try:
        articles = json_manager.read('articles')
        articles_data = articles.get('articles', [])
        
        # Find article by ID
        article = None
        for a in articles_data:
            if str(a.get('id')) == str(article_id):
                article = a
                break
        
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        # Prüfe erst, ob bereits vorgenerierte Previews existieren
        if article.get('link_previews'):
            logger.info(f"Using pre-generated previews for article {article_id}")
            return jsonify({'previews': article['link_previews']})
        
        # Fallback: Generiere Previews on-demand
        from app.utils.oembed_preview import get_fast_link_previews
        
        content = article.get('content', '') or ''
        previews = get_fast_link_previews(content)
        
        return jsonify({'previews': previews})
    except Exception as e:
        logger.error(f"Error getting preview for article {article_id}: {e}")
        return jsonify({'error': str(e)}), 500
