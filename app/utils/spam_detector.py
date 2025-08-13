"""
Automatische Spam-Erkennung für News-Artikel
"""

import re
from typing import Dict, List, Optional
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)


class SpamDetector:
    """
    Automatische Spam-Erkennung mit Pattern-Matching und Ähnlichkeitsvergleich
    """
    
    def __init__(self):
        # Spam-Patterns (Regex)
        self.spam_patterns = [
            # Krypto/Trading Spam
            r'(?i)(bitcoin|crypto|trading|gewinn|profit).*(?:jetzt|sofort|schnell)',
            r'(?i)🚀.*(?:moon|mond|explodiert|steigt)',
            r'(?i)(?:krypto|bitcoin|eth|trading).*(?:tipps?|signale?|gruppe)',
            
            # Werbung/Angebote
            r'(?i)(?:angebot|rabatt|sale|günstig).*(?:🔥|⚡|💥)',
            r'(?i)jetzt.*(?:kaufen|bestellen|sichern).*(?:nur|heute|begrenzt)',
            r'(?i)(?:gratis|kostenlos|umsonst).*(?:testen|probieren|holen)',
            
            # Telegram-Spam
            r'(?i)(?:kanal|channel|gruppe|group).*(?:beitreten|joinen|folgen)',
            r'(?i)(?:t\.me|telegram\.me)/[a-zA-Z0-9_]+',
            r'(?i)(?:mehr|weitere).*(?:infos?|informationen).*(?:hier|link)',
            
            # Clickbait
            r'(?i)(?:schock|skandal|unglaublich|sensation).*!+',
            r'(?i)das.*(?:glaubt|wusste|ahnt).*(?:niemand|keiner)',
            r'(?i)(?:ärzte|experten).*(?:hassen|verschweigen).*(?:trick|geheimnis)',
            
            # Excessive Emojis/Caps
            r'[🔥⚡💥🚀💎]{3,}',
            r'[A-Z]{10,}',
            r'!{3,}',
            
            # Affiliate/Referral Links
            r'(?i)(?:affiliate|ref|referral).*(?:link|code)',
            r'(?i)(?:bonus|cashback).*(?:code|link)',
        ]
        
        # Spam-Keywords (für Content-Analyse)
        self.spam_keywords = [
            'gewinnspiel', 'verlosung', 'teilnehmen', 'gewinnen',
            'rabattcode', 'gutschein', 'voucher', 'promo',
            'mlm', 'network marketing', 'passives einkommen',
            'reich werden', 'schnell geld', 'ohne arbeit',
            'klick hier', 'mehr dazu', 'link in bio',
            'dm mir', 'schreib mir', 'nachricht an',
        ]
        
        # Similarity threshold for duplicate detection
        self.similarity_threshold = 0.85
        
        # Recent articles cache for similarity comparison
        self.recent_articles = []
        self.max_recent_articles = 100
    
    def is_spam(self, article: Dict) -> Dict:
        """
        Prüft ob ein Artikel Spam ist
        
        Returns:
            Dict mit spam_score, is_spam, reasons
        """
        spam_score = 0
        reasons = []
        
        title = article.get('title', '').strip()
        content = article.get('content', '').strip()
        source = article.get('source', '').strip()
        
        # 1. Pattern-basierte Erkennung
        pattern_score, pattern_reasons = self._check_patterns(title, content)
        spam_score += pattern_score
        reasons.extend(pattern_reasons)
        
        # 2. Keyword-basierte Erkennung
        keyword_score, keyword_reasons = self._check_keywords(title, content)
        spam_score += keyword_score
        reasons.extend(keyword_reasons)
        
        # 3. Strukturelle Anomalien
        structure_score, structure_reasons = self._check_structure(title, content)
        spam_score += structure_score
        reasons.extend(structure_reasons)
        
        # 4. Ähnlichkeitsvergleich mit Recent Articles
        similarity_score, similarity_reasons = self._check_similarity(title, content)
        spam_score += similarity_score
        reasons.extend(similarity_reasons)
        
        # 5. Source-spezifische Checks
        source_score, source_reasons = self._check_source_patterns(source, title)
        spam_score += source_score
        reasons.extend(source_reasons)
        
        is_spam = spam_score >= 50  # Threshold: 50+ Punkte = Spam
        
        result = {
            'spam_score': spam_score,
            'is_spam': is_spam,
            'reasons': reasons,
            'confidence': min(spam_score / 100, 1.0)  # 0-1 scale
        }
        
        logger.info(f"Spam-Check für '{title[:50]}...': Score={spam_score}, Spam={is_spam}")
        if reasons:
            logger.info(f"Spam-Gründe: {', '.join(reasons)}")
        
        return result
    
    def _check_patterns(self, title: str, content: str) -> tuple:
        """Pattern-basierte Spam-Erkennung"""
        score = 0
        reasons = []
        text = f"{title} {content}"
        
        for pattern in self.spam_patterns:
            matches = re.findall(pattern, text)
            if matches:
                score += 20
                reasons.append(f"Spam-Pattern erkannt: {pattern[:30]}...")
        
        return score, reasons
    
    def _check_keywords(self, title: str, content: str) -> tuple:
        """Keyword-basierte Spam-Erkennung"""
        score = 0
        reasons = []
        text = f"{title} {content}".lower()
        
        keyword_count = sum(1 for keyword in self.spam_keywords if keyword in text)
        
        if keyword_count >= 3:
            score += 30
            reasons.append(f"Viele Spam-Keywords ({keyword_count})")
        elif keyword_count >= 1:
            score += 10
            reasons.append(f"Spam-Keywords gefunden ({keyword_count})")
        
        return score, reasons
    
    def _check_structure(self, title: str, content: str) -> tuple:
        """Strukturelle Anomalien erkennen"""
        score = 0
        reasons = []
        
        # Excessive emojis
        emoji_count = len(re.findall(r'[🔥⚡💥🚀💎💰💵🎯📈📊]', f"{title} {content}"))
        if emoji_count > 10:
            score += 25
            reasons.append(f"Excessive Emojis ({emoji_count})")
        elif emoji_count > 5:
            score += 10
            reasons.append(f"Viele Emojis ({emoji_count})")
        
        # ALL CAPS detection
        caps_ratio = len(re.findall(r'[A-Z]', title)) / max(len(title), 1)
        if caps_ratio > 0.7 and len(title) > 10:
            score += 20
            reasons.append("Übermäßige Großschreibung")
        
        # Excessive punctuation
        punct_count = len(re.findall(r'[!?]{2,}', f"{title} {content}"))
        if punct_count > 2:
            score += 15
            reasons.append(f"Excessive Punctuation ({punct_count})")
        
        # Very short content with links
        if len(content) < 50 and ('http' in content or 't.me' in content):
            score += 20
            reasons.append("Kurzer Content mit Links")
        
        return score, reasons
    
    def _check_similarity(self, title: str, content: str) -> tuple:
        """Ähnlichkeitsvergleich mit Recent Articles"""
        score = 0
        reasons = []
        
        current_text = f"{title} {content[:200]}".lower().strip()
        
        for recent_article in self.recent_articles:
            recent_text = f"{recent_article.get('title', '')} {recent_article.get('content', '')[:200]}".lower().strip()
            
            similarity = SequenceMatcher(None, current_text, recent_text).ratio()
            
            if similarity > self.similarity_threshold:
                score += 40
                reasons.append(f"Sehr ähnlich zu Recent Article ({similarity:.2f})")
                break
            elif similarity > 0.7:
                score += 15
                reasons.append(f"Ähnlich zu Recent Article ({similarity:.2f})")
        
        return score, reasons
    
    def _check_source_patterns(self, source: str, title: str) -> tuple:
        """Source-spezifische Spam-Patterns"""
        score = 0
        reasons = []
        
        # Bestimmte Source-Namen die oft Spam enthalten
        spam_source_patterns = [
            r'(?i)promo',
            r'(?i)offer',
            r'(?i)deal',
            r'(?i)ad[s]?$',
            r'(?i)affiliate'
        ]
        
        for pattern in spam_source_patterns:
            if re.search(pattern, source):
                score += 15
                reasons.append(f"Spam-verdächtige Quelle: {source}")
        
        return score, reasons
    
    def add_article_to_recent(self, article: Dict):
        """Fügt Artikel zur Recent-Liste für Similarity-Check hinzu"""
        self.recent_articles.append({
            'title': article.get('title', ''),
            'content': article.get('content', '')[:200],
            'id': article.get('id')
        })
        
        # Keep only recent articles
        if len(self.recent_articles) > self.max_recent_articles:
            self.recent_articles = self.recent_articles[-self.max_recent_articles:]
    
    def update_spam_patterns(self, new_patterns: List[str]):
        """Aktualisiert Spam-Patterns (für Admin-Interface)"""
        self.spam_patterns.extend(new_patterns)
        logger.info(f"Spam-Patterns aktualisiert: +{len(new_patterns)} Patterns")
    
    def get_spam_stats(self) -> Dict:
        """Statistiken über Spam-Erkennung"""
        return {
            'pattern_count': len(self.spam_patterns),
            'keyword_count': len(self.spam_keywords),
            'recent_articles_count': len(self.recent_articles),
            'similarity_threshold': self.similarity_threshold
        }


# Global Spam Detector Instance
spam_detector = SpamDetector()
