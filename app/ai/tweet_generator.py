"""
Tweet Generator Service
Kombiniert Artikel-Daten mit KI-generierten Tweets
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.data import json_manager
from app.ai.openai_client import OpenAIClient

logger = logging.getLogger(__name__)


class TweetGenerator:
    """Service für automatisierte Tweet-Generierung"""
    
    def __init__(self):
        self.openai_client = OpenAIClient()
    
    def generate_tweet_for_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        """
        Generiert Tweet für spezifischen Artikel
        
        Args:
            article_id: ID des Artikels
            
        Returns:
            Tweet-Daten oder None bei Fehler
        """
        try:
            # Artikel laden
            articles_data = json_manager.read('articles')
            articles = articles_data.get('articles', [])
            
            # Artikel finden
            article = None
            for art in articles:
                if art.get('id') == article_id:
                    article = art
                    break
            
            if not article:
                logger.error(f"Artikel {article_id} nicht gefunden")
                return None
            
            # Prüfe ob Artikel für Tweet geeignet ist
            if article.get('relevance_score') == 'spam':
                logger.info(f"Artikel {article_id} ist als Spam markiert - Skip Tweet-Generierung")
                return None
            
            # KI-Tweet generieren
            tweet_data = self.openai_client.generate_tweet(article)
            
            # Tweet-Objekt erstellen
            tweet_draft = {
                'id': str(uuid.uuid4()),
                'article_id': article_id,
                'article_title': article.get('title', ''),
                'article_url': article.get('url', ''),
                'article_source': article.get('source', article.get('channel', '')),
                'tweet_text': tweet_data.get('tweet_text', ''),
                'hashtags': tweet_data.get('hashtags', []),
                'mentions': tweet_data.get('mentions', []),
                'media_suggestion': tweet_data.get('media_suggestion', 'none'),
                'alternative_versions': tweet_data.get('alternative_versions', []),
                'created_at': datetime.now().isoformat(),
                'status': 'draft',  # draft, posted, archived
                'performance_score': None,  # Wird später bei Posting gesetzt
                'posted_at': None
            }
            
            # In tweets.json speichern
            self._save_tweet_draft(tweet_draft)
            
            logger.info(f"Tweet-Entwurf erstellt für Artikel {article_id}")
            return tweet_draft
            
        except Exception as e:
            logger.error(f"Fehler bei Tweet-Generierung für {article_id}: {e}")
            return None
    
    def generate_tweets_for_favorites(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Generiert Tweets für alle als 'favorite' markierten Artikel
        
        Args:
            limit: Maximale Anzahl Tweets zu generieren
            
        Returns:
            Liste der generierten Tweet-Entwürfe
        """
        try:
            # Artikel laden
            articles_data = json_manager.read('articles')
            articles = articles_data.get('articles', [])
            
            # Favorite-Artikel finden
            favorite_articles = [
                art for art in articles 
                if art.get('relevance_score') == 'favorite'
            ]
            
            # Nach Datum sortieren (neueste zuerst)
            favorite_articles.sort(
                key=lambda x: x.get('published_date', x.get('published_at', '')),
                reverse=True
            )
            
            # Limitieren
            favorite_articles = favorite_articles[:limit]
            
            logger.info(f"Generiere Tweets für {len(favorite_articles)} Favorite-Artikel")
            
            generated_tweets = []
            for article in favorite_articles:
                # Prüfe ob bereits Tweet existiert
                if self._has_existing_tweet(article.get('id')):
                    logger.info(f"Tweet für Artikel {article.get('id')} existiert bereits - Skip")
                    continue
                
                tweet = self.generate_tweet_for_article(article.get('id'))
                if tweet:
                    generated_tweets.append(tweet)
            
            logger.info(f"{len(generated_tweets)} neue Tweet-Entwürfe erstellt")
            return generated_tweets
            
        except Exception as e:
            logger.error(f"Fehler bei Batch-Tweet-Generierung: {e}")
            return []
    
    def get_tweet_drafts(self, status: str = None) -> List[Dict[str, Any]]:
        """
        Lädt Tweet-Entwürfe
        
        Args:
            status: Filter nach Status (draft, posted, archived)
            
        Returns:
            Liste der Tweet-Entwürfe
        """
        try:
            tweets_data = json_manager.read('tweets')
            tweets = tweets_data.get('tweets', [])
            
            if status:
                tweets = [t for t in tweets if t.get('status') == status]
            
            # Nach Erstellungsdatum sortieren (neueste zuerst)
            tweets.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            return tweets
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Tweet-Entwürfe: {e}")
            return []
    
    def update_tweet_status(self, tweet_id: str, status: str, posted_at: str = None) -> bool:
        """
        Aktualisiert Tweet-Status
        
        Args:
            tweet_id: ID des Tweets
            status: Neuer Status
            posted_at: Posting-Zeitstempel (optional)
            
        Returns:
            True bei Erfolg
        """
        try:
            tweets_data = json_manager.read('tweets')
            tweets = tweets_data.get('tweets', [])
            
            # Tweet finden und aktualisieren
            for tweet in tweets:
                if tweet.get('id') == tweet_id:
                    tweet['status'] = status
                    if posted_at:
                        tweet['posted_at'] = posted_at
                    break
            else:
                logger.error(f"Tweet {tweet_id} nicht gefunden")
                return False
            
            # Speichern
            json_manager.write('tweets', {'tweets': tweets})
            logger.info(f"Tweet {tweet_id} Status aktualisiert: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Tweet-Status-Update: {e}")
            return False
    
    def _save_tweet_draft(self, tweet_draft: Dict[str, Any]) -> None:
        """Speichert Tweet-Entwurf in tweets.json"""
        try:
            tweets_data = json_manager.read('tweets')
            tweets = tweets_data.get('tweets', [])
            
            # Neuen Tweet hinzufügen
            tweets.append(tweet_draft)
            
            # Speichern
            json_manager.write('tweets', {'tweets': tweets})
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Tweet-Entwurfs: {e}")
            raise
    
    def _has_existing_tweet(self, article_id: str) -> bool:
        """Prüft ob bereits Tweet für Artikel existiert"""
        try:
            tweets_data = json_manager.read('tweets')
            tweets = tweets_data.get('tweets', [])
            
            return any(t.get('article_id') == article_id for t in tweets)
            
        except Exception as e:
            logger.error(f"Fehler bei Tweet-Existenz-Prüfung: {e}")
            return False
