#!/usr/bin/env python3
"""
Script to add RSS sources for Apollo News, Tichy's Einblick, Reitschuster, and Fox News
"""

import json
import uuid
from datetime import datetime, timezone

def add_rss_sources():
    # RSS sources to add
    rss_sources = [
        {
            "name": "Apollo News RSS",
            "url": "https://apollo-news.net/feed/",
            "description": "Das Magazin für die Freiheit"
        },
        {
            "name": "Tichys Einblick RSS", 
            "url": "https://www.tichyseinblick.de/feed/",
            "description": "Liberal-konservativer Meinungsblog"
        },
        {
            "name": "Reitschuster.de RSS",
            "url": "https://reitschuster.de/feed/", 
            "description": "Kritischer Journalismus. Ohne Haltung. Ohne Belehrung. Ohne Ideologie."
        },
        {
            "name": "Fox News RSS",
            "url": "https://www.foxnews.com/rss",
            "description": "Latest & Breaking News on Fox News"
        }
    ]
    
    # Read current sources
    try:
        with open('/home/ga/ticker/data/sources.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"sources": []}
    
    # Check which sources already exist
    existing_urls = {source.get('url', '') for source in data['sources']}
    existing_names = {source.get('name', '') for source in data['sources']}
    
    added_count = 0
    
    for rss_source in rss_sources:
        # Skip if URL or name already exists
        if rss_source['url'] in existing_urls:
            print(f"RSS source '{rss_source['name']}' already exists (URL: {rss_source['url']})")
            continue
            
        if rss_source['name'] in existing_names:
            print(f"Source with name '{rss_source['name']}' already exists")
            continue
        
        # Create new source entry
        source_id = str(uuid.uuid4())
        current_time = datetime.now(timezone.utc).isoformat()
        
        new_source = {
            "id": source_id,
            "name": rss_source['name'],
            "type": "rss",
            "enabled": True,
            "created_at": current_time,
            "url": rss_source['url'],
            "update_interval": 30,
            "max_articles": 10,
            "config": {
                "url": rss_source['url'],
                "update_interval": 30,
                "max_articles": 10
            },
            "stats": {
                "last_scraped": None,
                "total_articles": 0,
                "error_count": 0,
                "last_error": None
            }
        }
        
        # Add to sources list
        data['sources'].append(new_source)
        added_count += 1
        print(f"Added RSS source: {rss_source['name']} ({rss_source['url']})")
    
    # Write back to file
    if added_count > 0:
        with open('/home/ga/ticker/data/sources.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\nSuccessfully added {added_count} RSS sources to sources.json")
    else:
        print("\nNo new sources were added (all already exist)")
    
    # Show status of automatic scraping
    enabled_count = sum(1 for source in data['sources'] if source.get('enabled', False))
    total_count = len(data['sources'])
    print(f"\nTotal sources: {total_count}")
    print(f"Enabled for automatic scraping: {enabled_count}")

if __name__ == "__main__":
    add_rss_sources()
