"""
OpenAI Client für KI-basierte Content-Bewertung und Tweet-Generierung
"""

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

import logging
from typing import Dict, Any, Optional, List
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI API Client für News-Bewertung und Tweet-Generierung"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            logger.warning("OPENAI_API_KEY nicht gesetzt - KI-Features deaktiviert")
            self.enabled = False
        else:
            openai.api_key = self.api_key
            self.enabled = True
            logger.info("OpenAI Client initialisiert")
    
    def evaluate_article_relevance(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Bewertet Artikel-Relevanz für Tweet-Generierung
        
        Returns:
            {
                'relevance_score': 'high|medium|low|spam',
                'tweet_worthy': True/False,
                'reasoning': 'Begründung',
                'suggested_tags': ['tag1', 'tag2']
            }
        """
        if not self.enabled:
            return {
                'relevance_score': 'medium',
                'tweet_worthy': False,
                'reasoning': 'KI-Bewertung nicht verfügbar (API-Key fehlt)',
                'suggested_tags': []
            }
        
        try:
            title = article.get('title', '')
            content = article.get('content', '')
            source = article.get('source', article.get('channel', ''))
            
            prompt = f"""
            Bewerte diesen Nachrichtenartikel für Social Media Relevanz:
            
            Quelle: {source}
            Titel: {title}
            Inhalt: {content[:500]}...
            
            Bewerte nach folgenden Kriterien:
            1. Nachrichtenwert und Aktualität
            2. Engagement-Potenzial für Twitter
            3. Glaubwürdigkeit und Faktenlage
            4. Spam/Clickbait-Faktor
            
            Antworte im JSON-Format:
            {{
                "relevance_score": "high|medium|low|spam",
                "tweet_worthy": true/false,
                "reasoning": "Begründung in 1-2 Sätzen",
                "suggested_tags": ["tag1", "tag2", "tag3"],
                "sentiment": "positive|neutral|negative"
            }}
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Du bist ein Experte für Social Media Content und Nachrichtenbewertung."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Versuche JSON zu parsen
            import json
            try:
                result = json.loads(result_text)
                logger.info(f"KI-Bewertung für Artikel {article.get('id', 'unknown')}: {result.get('relevance_score', 'unknown')}")
                return result
            except json.JSONDecodeError:
                logger.error(f"Konnte KI-Antwort nicht parsen: {result_text}")
                return {
                    'relevance_score': 'medium',
                    'tweet_worthy': False,
                    'reasoning': 'KI-Antwort konnte nicht verarbeitet werden',
                    'suggested_tags': []
                }
                
        except Exception as e:
            logger.error(f"Fehler bei KI-Bewertung: {e}")
            return {
                'relevance_score': 'medium',
                'tweet_worthy': False,
                'reasoning': f'Fehler bei KI-Bewertung: {str(e)}',
                'suggested_tags': []
            }
    
    def generate_tweet(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generiert Tweet-Text basierend auf Artikel
        
        Returns:
            {
                'tweet_text': 'Generated tweet text',
                'hashtags': ['#hashtag1', '#hashtag2'],
                'mentions': ['@mention'],
                'media_suggestion': 'image|video|none',
                'alternative_versions': ['version1', 'version2']
            }
        """
        if not self.enabled:
            return {
                'tweet_text': f"{article.get('title', '')[:200]}...",
                'hashtags': [],
                'mentions': [],
                'media_suggestion': 'none',
                'alternative_versions': []
            }
        
        try:
            title = article.get('title', '')
            content = article.get('content', '')
            source = article.get('source', article.get('channel', ''))
            url = article.get('url', '')
            
            prompt = f"""
            Erstelle einen engagierenden Twitter-Post für diesen Artikel:
            
            Titel: {title}
            Inhalt: {content[:400]}...
            Quelle: {source}
            URL: {url}
            
            Anforderungen:
            - Maximal 280 Zeichen
            - Aufmerksamkeitserregend aber seriös
            - Passende Hashtags (max. 3)
            - Call-to-Action
            - Deutscher Text
            
            Erstelle 3 alternative Versionen mit unterschiedlichen Stilen:
            1. Nachrichtenstil (sachlich)
            2. Engagement-fokussiert (emotional)
            3. Frage-basiert (diskussionsfördernd)
            
            Antworte im JSON-Format:
            {{
                "primary_tweet": "Hauptversion des Tweets",
                "hashtags": ["#hashtag1", "#hashtag2"],
                "alternatives": [
                    "Alternative Version 1",
                    "Alternative Version 2", 
                    "Alternative Version 3"
                ],
                "media_suggestion": "image|video|none"
            }}
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Du bist ein Social Media Manager mit Expertise für deutsche Twitter-Inhalte."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # JSON parsen
            import json
            try:
                result = json.loads(result_text)
                logger.info(f"Tweet generiert für Artikel {article.get('id', 'unknown')}")
                return {
                    'tweet_text': result.get('primary_tweet', title[:200]),
                    'hashtags': result.get('hashtags', []),
                    'mentions': [],
                    'media_suggestion': result.get('media_suggestion', 'none'),
                    'alternative_versions': result.get('alternatives', [])
                }
            except json.JSONDecodeError:
                logger.error(f"Konnte Tweet-JSON nicht parsen: {result_text}")
                # Fallback: Verwende direkte Antwort
                return {
                    'tweet_text': result_text[:280],
                    'hashtags': [],
                    'mentions': [],
                    'media_suggestion': 'none',
                    'alternative_versions': []
                }
                
        except Exception as e:
            logger.error(f"Fehler bei Tweet-Generierung: {e}")
            return {
                'tweet_text': f"📰 {title[:150]}... {url}",
                'hashtags': [],
                'mentions': [],
                'media_suggestion': 'none',
                'alternative_versions': []
            }
