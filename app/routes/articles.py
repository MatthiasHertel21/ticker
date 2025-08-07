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
    
    # Sortiere nach Datum (neueste zuerst)
    article_list = list(articles.get('articles', {}).values())
    article_list.sort(key=lambda x: x.get('published_at', ''), reverse=True)
    
    # Limitiere auf neueste 50
    article_list = article_list[:50]
    
    return render_template('articles.html', articles=article_list)


@bp.route('/rate/<article_id>', methods=['POST'])
def rate_article(article_id):
    """Bewerte einen Artikel"""
    try:
        data = request.get_json()
        rating = data.get('rating')
        
        if rating not in ['high', 'medium', 'low']:
            return jsonify({'success': False, 'error': 'Ungültiges Rating'})
        
        # Artikel laden und bewerten
        articles = json_manager.read('articles')
        if article_id not in articles.get('articles', {}):
            return jsonify({'success': False, 'error': 'Artikel nicht gefunden'})
        
        # Rating speichern
        articles['articles'][article_id]['relevance_score'] = rating
        articles['articles'][article_id]['rated_at'] = datetime.datetime.now().isoformat()
        
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
        if article_id not in articles.get('articles', {}):
            return jsonify({'success': False, 'error': 'Artikel nicht gefunden'})
        
        # Für Twitter markieren
        articles['articles'][article_id]['is_used_for_twitter'] = True
        articles['articles'][article_id]['marked_for_twitter_at'] = datetime.datetime.now().isoformat()
        
        json_manager.write('articles', articles)
        
        return jsonify({
            'success': True,
            'message': 'Artikel für Twitter markiert'
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Twitter-Markieren von Artikel {article_id}: {e}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/delete/<article_id>', methods=['DELETE'])
def delete_article(article_id):
    """Lösche einen Artikel"""
    try:
        json_manager.delete_item('articles', article_id)
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
