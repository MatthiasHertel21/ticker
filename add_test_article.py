#!/usr/bin/env python3

import json
import datetime

# Lade articles.json
with open('/home/ga/ticker/data/articles.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Erstelle Testartikel mit vorgenerierter Preview
test_article = {
    "id": "test_preview_demo_12345",
    "title": "Demo: Vorgenerierte Link-Previews beim Scraping",
    "content": "Dies ist ein Testartikel mit mehreren Links: https://www.youtube.com/watch?v=dQw4w9WgXcQ und https://www.tagesschau.de sowie https://twitter.com/example/status/123456789",
    "source": "Test - Demo",
    "channel": "demo",
    "url": "https://example.com/demo",
    "published_date": datetime.datetime.now().isoformat(),
    "scraped_date": datetime.datetime.now().isoformat(),
    "platform": "demo",
    "message_age": "recent",
    "link_previews": [
        {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "title": "Rick Astley - Never Gonna Give You Up (Official Video)",
            "description": "The official video for Never Gonna Give You Up by Rick Astley.",
            "image": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
            "site_name": "YouTube",
            "favicon": "https://www.google.com/s2/favicons?domain=youtube.com",
            "type": "oembed",
            "html": "<iframe width=\"560\" height=\"315\" src=\"https://www.youtube.com/embed/dQw4w9WgXcQ\" frameborder=\"0\" allowfullscreen></iframe>"
        },
        {
            "url": "https://www.tagesschau.de",
            "title": "tagesschau.de - Nachrichten",
            "description": "Aktuelle Nachrichten, Informationen und Videos aus Deutschland und der Welt.",
            "image": "https://www.tagesschau.de/multimedia/bilder/tagesschau-logo-103~_v-grossgalerie16x9.jpg",
            "site_name": "tagesschau.de",
            "favicon": "https://www.google.com/s2/favicons?domain=tagesschau.de",
            "type": "meta"
        }
    ]
}

# Füge den Artikel am Anfang der Liste hinzu
data["articles"].insert(0, test_article)

# Speichere zurück
with open('/home/ga/ticker/data/articles.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("✅ Testartikel mit vorgenerierten Previews hinzugefügt!")
