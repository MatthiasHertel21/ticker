#!/usr/bin/env python3
"""
Migration Script: Telegram-Quellen von Dictionary- zu Listen-Format konvertieren
"""
import json
from datetime import datetime

def migrate_telegram_sources():
    # Backup laden
    with open('/home/ga/ticker/data/backups/sources_20250810_135552.json', 'r', encoding='utf-8') as f:
        backup_data = json.load(f)
    
    # Aktuelle sources.json laden
    with open('/home/ga/ticker/data/sources.json', 'r', encoding='utf-8') as f:
        current_data = json.load(f)
    
    # Telegram-Quellen aus Backup extrahieren und konvertieren
    telegram_sources = []
    for source_id, source_data in backup_data['sources'].items():
        if source_data.get('type') == 'telegram':
            # Neue Struktur für Multi-Source-System
            converted_source = {
                'id': source_data['id'],
                'name': source_data['name'],
                'type': 'telegram',
                'enabled': source_data.get('is_active', True),
                'created_at': source_data.get('created_at', source_data.get('added_at')),
                'config': {
                    'channel_username': source_data['channel_username'],
                    'channel_id': source_data.get('channel_id'),
                    'keywords': source_data.get('keywords', []),
                    'exclude_keywords': source_data.get('exclude_keywords', []),
                    'last_message_id': source_data.get('last_message_id', 0)
                },
                'stats': {
                    'last_scraped': None,
                    'total_articles': 0,
                    'error_count': 0,
                    'last_error': None
                }
            }
            telegram_sources.append(converted_source)
    
    # Telegram-Quellen zu aktueller Liste hinzufügen
    current_data['sources'].extend(telegram_sources)
    current_data['last_updated'] = datetime.now().isoformat()
    
    # Backup der aktuellen Datei erstellen
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'/home/ga/ticker/data/backups/sources_migration_{timestamp}.json'
    with open(backup_filename, 'w', encoding='utf-8') as f:
        json.dump(current_data, f, indent=2, ensure_ascii=False)
    
    # Neue Datei schreiben
    with open('/home/ga/ticker/data/sources.json', 'w', encoding='utf-8') as f:
        json.dump(current_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Migration abgeschlossen:")
    print(f"   - {len(telegram_sources)} Telegram-Quellen wiederhergestellt")
    print(f"   - Backup erstellt: {backup_filename}")
    
    # Liste der wiederhergestellten Kanäle anzeigen
    print("\n📺 Wiederhergestellte Telegram-Kanäle:")
    for source in telegram_sources:
        status = "🟢 Aktiv" if source['enabled'] else "🔴 Inaktiv"
        print(f"   {status} {source['name']} (@{source['config']['channel_username']})")

if __name__ == "__main__":
    migrate_telegram_sources()
