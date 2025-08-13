#!/usr/bin/env python3
"""
Script to add the remaining RSS sources to the ticker system.
Based on research results from RSS feed discovery.
"""

import json
import uuid
from datetime import datetime

def load_sources():
    """Load existing sources from JSON file."""
    try:
        with open('data/sources.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Handle both formats: direct array or nested object with 'sources' key
            if isinstance(data, dict) and 'sources' in data:
                return data['sources']
            elif isinstance(data, list):
                return data
            else:
                return []
    except FileNotFoundError:
        return []

def save_sources(sources):
    """Save sources to JSON file."""
    # Maintain the nested structure if it exists
    try:
        with open('data/sources.json', 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        
        if isinstance(existing_data, dict) and 'sources' in existing_data:
            # Preserve existing structure with 'sources' wrapper
            existing_data['sources'] = sources
            with open('data/sources.json', 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
        else:
            # Save as direct array
            with open('data/sources.json', 'w', encoding='utf-8') as f:
                json.dump(sources, f, indent=2, ensure_ascii=False)
    except FileNotFoundError:
        # Create new file with sources wrapper
        data = {"sources": sources}
        with open('data/sources.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

def source_exists(sources, url):
    """Check if a source with the given URL already exists."""
    for source in sources:
        # Handle different URL field names
        source_url = source.get('url') or source.get('config', {}).get('url')
        if source_url == url:
            return True
    return False

def create_rss_source(name, url, description):
    """Create a new RSS source configuration matching the existing format."""
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "type": "rss",
        "enabled": True,
        "created_at": datetime.now().isoformat(),
        "url": url,
        "update_interval": 30,
        "max_articles": 10,
        "config": {
            "url": url,
            "update_interval": 30,
            "max_articles": 10,
            "description": description
        },
        "stats": {
            "last_scraped": None,
            "total_articles": 0,
            "error_count": 0,
            "last_error": None
        }
    }

def main():
    # Load existing sources
    sources = load_sources()
    print(f"Currently have {len(sources)} sources")
    
    # Define the new RSS sources to add (based on research results)
    new_sources = [
        {
            "name": "Rubikon",
            "url": "https://www.rubikon.news/feed",
            "description": "Magazin für die kritische Masse - Alternative Nachrichten und Meinungen"
        },
        {
            "name": "NachDenkSeiten",
            "url": "https://www.nachdenkseiten.de/?feed=rss2",
            "description": "Kritische Nachrichten und Meinungen zu Politik, Wirtschaft und Gesellschaft"
        },
        {
            "name": "Achgut",
            "url": "https://www.achgut.com/rss.xml",
            "description": "Die Achse des Guten - Politischer Blog und Meinungsportal"
        },
        {
            "name": "NIUS",
            "url": "https://www.nius.de/feed",
            "description": "Unabhängiger Journalismus und kritische Berichterstattung"
        },
        {
            "name": "Alexander Wallasch",
            "url": "https://alexander-wallasch.de/feed",
            "description": "Politischer Blog und Kommentare von Alexander Wallasch"
        },
        {
            "name": "Apolut",
            "url": "https://apolut.net/feed/",
            "description": "Unabhängige Nachrichten und Berichte - Alternative Medienplattform"
        },
        {
            "name": "Transition News",
            "url": "https://transition-news.org/spip.php?page=backend",
            "description": "Nachrichten für eine Welt im Wandel - Alternative Berichterstattung"
        },
        {
            "name": "Report24",
            "url": "https://report24.news/feed/",
            "description": "Der Wahrheit verpflichtet - Unabhängiger Journalismus"
        }
    ]
    
    # Add new sources if they don't already exist
    added_count = 0
    skipped_count = 0
    
    for source_info in new_sources:
        if source_exists(sources, source_info["url"]):
            print(f"⚠️  Source '{source_info['name']}' already exists, skipping...")
            skipped_count += 1
        else:
            new_source = create_rss_source(
                source_info["name"],
                source_info["url"],
                source_info["description"]
            )
            sources.append(new_source)
            print(f"✅ Added RSS source: {source_info['name']}")
            print(f"   URL: {source_info['url']}")
            print(f"   Description: {source_info['description']}")
            added_count += 1
    
    # Save updated sources
    if added_count > 0:
        save_sources(sources)
        print(f"\n🎉 Successfully added {added_count} new RSS sources!")
        print(f"📊 Total sources now: {len(sources)}")
    else:
        print(f"\n✨ No new sources added - all sources already exist")
    
    if skipped_count > 0:
        print(f"🔄 Skipped {skipped_count} existing sources")
    
    print(f"\n📈 Summary:")
    print(f"   - RSS sources added: {added_count}")
    print(f"   - Sources skipped: {skipped_count}")
    print(f"   - Total sources: {len(sources)}")
    
    # Show RSS sources in system
    rss_sources = [s for s in sources if s.get('type') == 'rss']
    print(f"\n📰 All RSS sources in system ({len(rss_sources)}):")
    for i, source in enumerate(rss_sources, 1):
        status = "✅ Active" if source.get('enabled', source.get('active', False)) else "❌ Inactive"
        source_url = source.get('url') or source.get('config', {}).get('url', 'No URL')
        print(f"   {i:2d}. {source['name']:20s} - {status}")
        print(f"       {source_url}")

if __name__ == "__main__":
    main()
