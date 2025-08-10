"""
Tweet Management Routes
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from app.ai.tweet_generator import TweetGenerator
from app.data import json_manager
import logging
from datetime import datetime

bp = Blueprint('tweets', __name__, url_prefix='/tweets')
logger = logging.getLogger(__name__)

tweet_generator = TweetGenerator()


@bp.route('/')
def tweets_dashboard():
    """Tweet-Dashboard mit allen Entwürfen"""
    try:
        # Tweet-Entwürfe laden
        tweet_drafts = tweet_generator.get_tweet_drafts()
        
        # Statistiken berechnen
        stats = {
            'total_drafts': len(tweet_drafts),
            'draft_count': len([t for t in tweet_drafts if t.get('status') == 'draft']),
            'posted_count': len([t for t in tweet_drafts if t.get('status') == 'posted']),
            'archived_count': len([t for t in tweet_drafts if t.get('status') == 'archived'])
        }
        
        return render_template('tweets/dashboard.html', 
                             tweets=tweet_drafts, 
                             stats=stats)
                             
    except Exception as e:
        logger.error(f"Fehler im Tweet-Dashboard: {e}")
        flash(f'Fehler beim Laden der Tweets: {e}', 'error')
        return render_template('tweets/dashboard.html', tweets=[], stats={})


@bp.route('/generate', methods=['POST'])
def generate_tweets():
    """Generiert Tweets für Favorite-Artikel"""
    try:
        limit = int(request.form.get('limit', 10))
        
        # Tweets für Favorites generieren
        generated_tweets = tweet_generator.generate_tweets_for_favorites(limit=limit)
        
        flash(f'{len(generated_tweets)} neue Tweet-Entwürfe erstellt!', 'success')
        return redirect(url_for('tweets.tweets_dashboard'))
        
    except Exception as e:
        logger.error(f"Fehler bei Tweet-Generierung: {e}")
        flash(f'Fehler bei Tweet-Generierung: {e}', 'error')
        return redirect(url_for('tweets.tweets_dashboard'))


@bp.route('/generate/<article_id>', methods=['POST'])
def generate_tweet_for_article(article_id):
    """Generiert Tweet für spezifischen Artikel"""
    try:
        tweet = tweet_generator.generate_tweet_for_article(article_id)
        
        if tweet:
            return jsonify({
                'success': True,
                'tweet': tweet,
                'message': 'Tweet-Entwurf erstellt!'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Tweet konnte nicht generiert werden'
            }), 400
            
    except Exception as e:
        logger.error(f"Fehler bei Tweet-Generierung für {article_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/update-status/<tweet_id>', methods=['POST'])
def update_tweet_status(tweet_id):
    """Aktualisiert Tweet-Status"""
    try:
        data = request.get_json()
        status = data.get('status')
        
        if status not in ['draft', 'posted', 'archived']:
            return jsonify({
                'success': False,
                'error': 'Ungültiger Status'
            }), 400
        
        posted_at = None
        if status == 'posted':
            posted_at = datetime.now().isoformat()
        
        success = tweet_generator.update_tweet_status(tweet_id, status, posted_at)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Status auf "{status}" aktualisiert'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Tweet nicht gefunden'
            }), 404
            
    except Exception as e:
        logger.error(f"Fehler bei Status-Update für {tweet_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/copy/<tweet_id>')
def copy_tweet(tweet_id):
    """Bereitet Tweet-Text zum Kopieren vor"""
    try:
        tweets_data = json_manager.read('tweets')
        tweets = tweets_data.get('tweets', [])
        
        tweet = next((t for t in tweets if t.get('id') == tweet_id), None)
        if not tweet:
            flash('Tweet nicht gefunden', 'error')
            return redirect(url_for('tweets.tweets_dashboard'))
        
        # Tweet-Text mit Hashtags kombinieren
        tweet_text = tweet.get('tweet_text', '')
        hashtags = tweet.get('hashtags', [])
        
        if hashtags:
            tweet_text += ' ' + ' '.join(hashtags)
        
        return render_template('tweets/copy.html', 
                             tweet=tweet, 
                             tweet_text=tweet_text)
                             
    except Exception as e:
        logger.error(f"Fehler beim Tweet-Kopieren für {tweet_id}: {e}")
        flash(f'Fehler: {e}', 'error')
        return redirect(url_for('tweets.tweets_dashboard'))


@bp.route('/api/stats')
def api_tweet_stats():
    """API-Endpoint für Tweet-Statistiken"""
    try:
        tweets = tweet_generator.get_tweet_drafts()
        
        stats = {
            'total': len(tweets),
            'draft': len([t for t in tweets if t.get('status') == 'draft']),
            'posted': len([t for t in tweets if t.get('status') == 'posted']),
            'archived': len([t for t in tweets if t.get('status') == 'archived']),
            'recent_count': len([t for t in tweets if t.get('created_at', '').startswith(datetime.now().strftime('%Y-%m-%d'))])
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Fehler bei Tweet-Statistiken: {e}")
        return jsonify({'error': str(e)}), 500
