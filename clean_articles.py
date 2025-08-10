#!/usr/bin/env python3
"""
JSON-Bereinigung für doppelte und leere Artikel
"""

import json
import sys
from datetime import datetime
import argparse

def load_articles():
    """Lädt die Artikel-Daten"""
    try:
        with open('data/articles.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Fehler beim Laden: {e}")
        return None

def save_articles(data):
    """Speichert die Artikel-Daten"""
    try:
        # Backup erstellen
        backup_name = f"data/backups/articles_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_name, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Backup erstellt: {backup_name}")
        
        # Originaldatei überschreiben
        with open('data/articles.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Bereinigte Datei gespeichert")
        
    except Exception as e:
        print(f"Fehler beim Speichern: {e}")
        return False
    return True

def clean_articles(data, remove_empty=True, remove_duplicates=True, min_content_length=10):
    """Bereinigt die Artikel"""
    articles = data.get('articles', [])
    original_count = len(articles)
    
    cleaned_articles = []
    seen_content = set()
    stats = {
        'original_count': original_count,
        'removed_empty': 0,
        'removed_short': 0,
        'removed_duplicates': 0,
        'final_count': 0
    }
    
    for article in articles:
        content = article.get('content', '').strip()
        title = article.get('title', '').strip()
        
        # Entferne komplett leere Artikel
        if remove_empty and not content and not title:
            stats['removed_empty'] += 1
            continue
        
        # Entferne zu kurze Artikel (nur Tags/Hashtags)
        if len(content) < min_content_length and len(title) < 10:
            stats['removed_short'] += 1
            continue
        
        # Entferne Duplikate basierend auf Inhalt
        if remove_duplicates:
            content_key = f"{title}|{content}"
            if content_key in seen_content:
                stats['removed_duplicates'] += 1
                continue
            seen_content.add(content_key)
        
        cleaned_articles.append(article)
    
    stats['final_count'] = len(cleaned_articles)
    data['articles'] = cleaned_articles
    
    # Update metadata
    if 'metadata' not in data:
        data['metadata'] = {}
    data['metadata']['last_cleaned'] = datetime.now().isoformat()
    data['metadata']['cleanup_stats'] = stats
    
    return data, stats

def analyze_articles(data):
    """Analysiert die Artikel ohne Änderungen"""
    articles = data.get('articles', [])
    
    stats = {
        'total_articles': len(articles),
        'empty_content': 0,
        'short_content': 0,
        'duplicate_content': 0,
        'platforms': {},
        'channels': {}
    }
    
    seen_content = set()
    
    for article in articles:
        content = article.get('content', '').strip()
        title = article.get('title', '').strip()
        platform = article.get('platform', 'unknown')
        channel = article.get('channel', 'unknown')
        
        # Statistiken sammeln
        if not content and not title:
            stats['empty_content'] += 1
        
        if len(content) < 10 and len(title) < 10:
            stats['short_content'] += 1
        
        content_key = f"{title}|{content}"
        if content_key in seen_content:
            stats['duplicate_content'] += 1
        seen_content.add(content_key)
        
        # Platform/Channel stats
        stats['platforms'][platform] = stats['platforms'].get(platform, 0) + 1
        stats['channels'][channel] = stats['channels'].get(channel, 0) + 1
    
    return stats

def main():
    parser = argparse.ArgumentParser(description='JSON-Artikel bereinigen')
    parser.add_argument('--analyze', action='store_true', help='Nur analysieren, nicht bereinigen')
    parser.add_argument('--clean', action='store_true', help='Artikel bereinigen')
    parser.add_argument('--min-length', type=int, default=10, help='Minimale Content-Länge')
    parser.add_argument('--keep-duplicates', action='store_true', help='Duplikate behalten')
    parser.add_argument('--keep-empty', action='store_true', help='Leere Artikel behalten')
    
    args = parser.parse_args()
    
    # Lade Daten
    data = load_articles()
    if not data:
        sys.exit(1)
    
    if args.analyze:
        print("📊 Artikel-Analyse:")
        stats = analyze_articles(data)
        print(f"Total Artikel: {stats['total_articles']}")
        print(f"Leere Artikel: {stats['empty_content']}")
        print(f"Kurze Artikel: {stats['short_content']}")
        print(f"Duplikate: {stats['duplicate_content']}")
        print(f"\nPlattformen: {dict(list(stats['platforms'].items())[:5])}")
        print(f"Top Kanäle: {dict(list(sorted(stats['channels'].items(), key=lambda x: x[1], reverse=True))[:5])}")
    
    elif args.clean:
        print("🧹 Bereinige Artikel...")
        cleaned_data, stats = clean_articles(
            data, 
            remove_empty=not args.keep_empty,
            remove_duplicates=not args.keep_duplicates,
            min_content_length=args.min_length
        )
        
        print(f"📊 Bereinigungs-Statistik:")
        print(f"Ursprünglich: {stats['original_count']} Artikel")
        print(f"Entfernt - Leer: {stats['removed_empty']}")
        print(f"Entfernt - Zu kurz: {stats['removed_short']}")
        print(f"Entfernt - Duplikate: {stats['removed_duplicates']}")
        print(f"Verbleibend: {stats['final_count']} Artikel")
        print(f"Einsparung: {stats['original_count'] - stats['final_count']} Artikel")
        
        if save_articles(cleaned_data):
            print("✅ Bereinigung erfolgreich abgeschlossen!")
        else:
            print("❌ Fehler beim Speichern!")
            sys.exit(1)
    
    else:
        print("Bitte --analyze oder --clean angeben")
        print("Beispiele:")
        print("  python3 clean_articles.py --analyze")
        print("  python3 clean_articles.py --clean")
        print("  python3 clean_articles.py --clean --min-length 20")

if __name__ == '__main__':
    main()
