"""
Housekeeping-Übersicht Script
"""

import sys
import os
from datetime import datetime, timedelta

# Füge app zum Python Path hinzu
sys.path.insert(0, '/app')

from app.data.json_manager import JSONManager
from config.config import Config


def main():
    print("🧹 Ticker Housekeeping - Übersicht")
    print("=" * 50)
    
    # JSON Manager initialisieren
    json_manager = JSONManager()
    
    # Aktuelle Konfiguration anzeigen
    print(f"\n📋 Aktuelle Konfiguration:")
    print(f"├─ Cleanup-Regel: {Config.CLEANUP_DAYS} Tage")
    print(f"├─ Backup-Retention: {getattr(Config, 'BACKUP_RETENTION_DAYS', 7)} Tage")
    print(f"├─ Auto-Cleanup: {getattr(Config, 'HOUSEKEEPING_ENABLED', True)}")
    print(f"└─ Auto-Backup: {getattr(Config, 'AUTO_BACKUP', True)}")
    
    try:
        # Artikel-Statistiken
        articles = json_manager.read('articles')
        articles_data = articles.get('articles', [])
        total_articles = len(articles_data)
        
        print(f"\n📊 Artikel-Statistiken:")
        print(f"├─ Gesamt: {total_articles} Artikel")
        
        if total_articles > 0:
            # Analysiere Alter
            cutoff_date = datetime.now() - timedelta(days=Config.CLEANUP_DAYS)
            old_articles = 0
            dates = []
            
            for article in articles_data:
                try:
                    scraped_date_str = article.get('scraped_date', article.get('published_date', ''))
                    if scraped_date_str:
                        scraped_date = datetime.fromisoformat(scraped_date_str.replace('Z', '+00:00').replace('+00:00', ''))
                        dates.append(scraped_date)
                        if scraped_date < cutoff_date:
                            old_articles += 1
                except:
                    continue
            
            if dates:
                dates.sort()
                oldest = dates[0]
                newest = dates[-1]
                age_days = (datetime.now() - oldest).days
                
                print(f"├─ Ältester: {oldest.strftime('%Y-%m-%d %H:%M')} ({age_days} Tage)")
                print(f"├─ Neuester: {newest.strftime('%Y-%m-%d %H:%M')}")
                print(f"├─ Zeitraum: {(newest - oldest).days} Tage")
                print(f"├─ Zu löschen (>{Config.CLEANUP_DAYS} Tage): {old_articles}")
                print(f"└─ Verbleiben: {total_articles - old_articles}")
                
                if old_articles > 0:
                    print(f"\n⚠️  {old_articles} Artikel sind älter als {Config.CLEANUP_DAYS} Tage und würden gelöscht werden!")
                else:
                    print(f"\n✅ Alle Artikel sind jünger als {Config.CLEANUP_DAYS} Tage - keine Bereinigung nötig")
            else:
                print("└─ Keine gültigen Datumsangaben gefunden")
        else:
            print("└─ Keine Artikel vorhanden")
        
        # Quellenverteilung
        sources = {}
        for article in articles_data:
            source = article.get('channel', 'Unbekannt')
            sources[source] = sources.get(source, 0) + 1
        
        if sources:
            print(f"\n📡 Top-Quellen:")
            sorted_sources = sorted(sources.items(), key=lambda x: x[1], reverse=True)
            for i, (source, count) in enumerate(sorted_sources[:5]):
                prefix = "├─" if i < 4 else "└─"
                print(f"{prefix} {source}: {count} Artikel")
        
        # Speicher-Verwendung (approximiert)
        try:
            articles_file = f"{json_manager.data_dir}/articles.json"
            if os.path.exists(articles_file):
                size_mb = os.path.getsize(articles_file) / (1024 * 1024)
                print(f"\n💾 Speicher-Verwendung:")
                print(f"└─ articles.json: {size_mb:.2f} MB")
        except:
            pass
        
    except Exception as e:
        print(f"\n❌ Fehler beim Laden der Statistiken: {e}")
    
    print(f"\n🕒 Stand: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
