#!/usr/bin/env python3
"""
CLI Tool für Housekeeping-Operationen
Ermöglicht manuelle Bereinigung ohne Web-Interface
"""

import sys
import json
import argparse
from datetime import datetime, timedelta

# Import der Anwendung
sys.path.insert(0, '/app')
from app.tasks.housekeeping_tasks import HousekeepingManager
from config.config import Config


def main():
    parser = argparse.ArgumentParser(
        description='Ticker Housekeeping CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Beispiele:
  %(prog)s --status                    # Zeige Speicher-Statistiken
  %(prog)s --cleanup-articles          # Bereinige alte Artikel
  %(prog)s --cleanup-articles --days 60   # Bereinige Artikel älter als 60 Tage
  %(prog)s --cleanup-media             # Entferne verwaiste Media-Files
  %(prog)s --cleanup-backups           # Bereinige alte Backups
  %(prog)s --full-cleanup              # Vollständige Bereinigung
  %(prog)s --dry-run --cleanup-articles   # Simulation ohne Änderungen
        '''
    )
    
    # Aktions-Optionen
    parser.add_argument('--status', action='store_true',
                       help='Zeige aktuelle Speicher-Statistiken')
    parser.add_argument('--cleanup-articles', action='store_true',
                       help='Bereinige alte Artikel')
    parser.add_argument('--cleanup-media', action='store_true',
                       help='Entferne verwaiste Media-Files')
    parser.add_argument('--cleanup-backups', action='store_true',
                       help='Bereinige alte Backups')
    parser.add_argument('--full-cleanup', action='store_true',
                       help='Führe vollständige Bereinigung durch')
    
    # Parameter-Optionen
    parser.add_argument('--days', type=int, 
                       help='Anzahl Tage für Bereinigung (überschreibt Config)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Simulation ohne tatsächliche Änderungen')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Ausführliche Ausgabe')
    parser.add_argument('--json-output', action='store_true',
                       help='Ausgabe als JSON für Automatisierung')
    
    args = parser.parse_args()
    
    # Mindestens eine Aktion erforderlich
    if not any([args.status, args.cleanup_articles, args.cleanup_media, 
                args.cleanup_backups, args.full_cleanup]):
        parser.print_help()
        sys.exit(1)
    
    # Housekeeping Manager initialisieren
    manager = HousekeepingManager()
    
    # Ergebnisse sammeln
    results = {}
    
    try:
        # Status anzeigen
        if args.status:
            if args.verbose:
                print("📊 Lade Speicher-Statistiken...")
            
            stats = manager.get_storage_stats()
            results['storage_stats'] = stats
            
            if not args.json_output:
                print_storage_stats(stats, args.verbose)
        
        # Artikel bereinigen
        if args.cleanup_articles:
            if args.verbose:
                print(f"🧹 Starte Artikel-Bereinigung...")
            
            if args.dry_run:
                print("🔍 DRY-RUN: Keine tatsächlichen Änderungen")
                # Für Dry-Run: Analysiere ohne zu löschen
                articles_data = manager.json_manager.load_data('articles')
                days = args.days or Config.CLEANUP_DAYS
                cutoff_date = datetime.now() - timedelta(days=days)
                
                old_articles = []
                for article in articles_data.get('articles', []):
                    try:
                        scraped_date = datetime.fromisoformat(
                            article.get('scraped_date', '').replace('Z', '+00:00').replace('+00:00', '')
                        )
                        if scraped_date < cutoff_date:
                            old_articles.append(article)
                    except:
                        pass
                
                results['articles_cleanup'] = {
                    'would_remove_count': len(old_articles),
                    'cutoff_date': cutoff_date.isoformat(),
                    'dry_run': True
                }
                
                if not args.json_output:
                    print(f"📋 Würde {len(old_articles)} Artikel entfernen")
            else:
                result = manager.cleanup_old_articles(args.days)
                results['articles_cleanup'] = result
                
                if not args.json_output:
                    print(f"✅ {result['removed_count']} Artikel entfernt")
        
        # Media bereinigen
        if args.cleanup_media:
            if args.verbose:
                print("🧹 Starte Media-Bereinigung...")
            
            if not args.dry_run:
                result = manager.cleanup_orphaned_media()
                results['media_cleanup'] = result
                
                if not args.json_output:
                    print(f"✅ {result['removed_count']} verwaiste Media-Files entfernt")
            else:
                if not args.json_output:
                    print("🔍 DRY-RUN: Media-Analyse würde durchgeführt")
        
        # Backups bereinigen
        if args.cleanup_backups:
            if args.verbose:
                print("🧹 Starte Backup-Bereinigung...")
            
            if not args.dry_run:
                result = manager.cleanup_old_backups(args.days)
                results['backup_cleanup'] = result
                
                if not args.json_output:
                    print(f"✅ {result['removed_count']} Backups entfernt ({result['size_freed_mb']} MB)")
            else:
                if not args.json_output:
                    print("🔍 DRY-RUN: Backup-Analyse würde durchgeführt")
        
        # Vollständige Bereinigung
        if args.full_cleanup:
            if args.verbose:
                print("🚀 Starte vollständige Bereinigung...")
            
            if not args.dry_run:
                result = manager.full_cleanup()
                results['full_cleanup'] = result
                
                if not args.json_output:
                    print(f"✅ Vollständige Bereinigung abgeschlossen")
                    print(f"   Artikel: {result['articles_cleanup']['removed_count']}")
                    print(f"   Media: {result['orphaned_media_cleanup']['removed_count']}")
                    print(f"   Backups: {result['backup_cleanup']['removed_count']}")
                    print(f"   Gespart: {result['storage_saved_mb']} MB")
            else:
                if not args.json_output:
                    print("🔍 DRY-RUN: Vollständige Analyse würde durchgeführt")
        
        # Ausgabe
        if args.json_output:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        elif args.verbose:
            print("\n🏁 Housekeeping abgeschlossen")
    
    except Exception as e:
        if args.json_output:
            print(json.dumps({'error': str(e)}, indent=2))
        else:
            print(f"❌ Fehler: {e}")
        sys.exit(1)


def print_storage_stats(stats, verbose=False):
    """Formatierte Ausgabe der Speicher-Statistiken"""
    print("\n📊 Speicher-Statistiken")
    print("=" * 50)
    
    # Artikel
    print(f"📰 Artikel:")
    print(f"   Anzahl: {stats['articles']['count']:,}")
    print(f"   Größe:  {stats['articles']['size_mb']:.1f} MB")
    
    # Media
    print(f"🖼️  Media-Files:")
    print(f"   Anzahl: {stats['media']['count']:,}")
    print(f"   Größe:  {stats['media']['size_mb']:.1f} MB")
    
    # Backups
    print(f"💾 Backups:")
    print(f"   Anzahl: {stats['backups']['count']:,}")
    print(f"   Größe:  {stats['backups']['size_mb']:.1f} MB")
    
    # Total
    print(f"📦 Gesamt:")
    print(f"   Größe:  {stats['total']['size_mb']:.1f} MB ({stats['total']['size_gb']:.2f} GB)")
    
    if verbose:
        print(f"\n⏰ Generiert: {stats['generated_at']}")
    
    # Status-Indikatoren
    article_status = "🟢" if stats['articles']['count'] < 1000 else "🟡" if stats['articles']['count'] < 2000 else "🔴"
    media_status = "🟢" if stats['media']['count'] < 100 else "🟡" if stats['media']['count'] < 500 else "🔴"
    backup_status = "🟢" if stats['backups']['count'] < 50 else "🟡" if stats['backups']['count'] < 100 else "🔴"
    
    print(f"\n📈 Status: {article_status} Artikel, {media_status} Media, {backup_status} Backups")


if __name__ == '__main__':
    main()
