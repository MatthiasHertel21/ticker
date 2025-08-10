"""
Template-Filter für bessere Content-Darstellung
"""

import re
from markupsafe import Markup
from urllib.parse import urlparse


def get_link_previews(content):
    """Generiert Link-Previews für Content"""
    try:
        from app.utils.link_preview import link_preview_generator
        return link_preview_generator.generate_previews_for_article(content)
    except Exception as e:
        return []


def clean_url_text(url):
    """Bereinigt URL für Anzeige"""
    if not url:
        return ""
    
    # Entferne Protokoll
    cleaned = url.replace('https://', '').replace('http://', '')
    
    # Entferne www.
    if cleaned.startswith('www.'):
        cleaned = cleaned[4:]
    
    # Kürze sehr lange URLs
    if len(cleaned) > 40:
        cleaned = cleaned[:37] + '...'
    
    return cleaned


def render_telegram_content_clean(content):
    """
    Rendert Telegram-Content und entfernt URLs am Anfang
    """
    if not content:
        return ""
    
    # Entferne URL am Anfang des Contents
    content = re.sub(r'^https?://[^\s\n]+\n*', '', content)
    
    # Verwende die normale render_telegram_content Funktion
    return render_telegram_content(content)


def render_telegram_content(content):
    """
    Rendert Telegram-Content mit:
    - Klickbare Links
    - Bilder als Embedded Images oder Placeholders
    - Basic Markup (fett, kursiv)
    - Zeilenumbrüche
    """
    if not content:
        return ""
    
    # Falls der Content bereits escaped ist, unescape ihn zunächst
    if '&lt;' in content or '&gt;' in content or '&amp;' in content:
        content = content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    
    # Entferne "[Zum Artikel]" und ähnliche Phrasen
    import re
    content = re.sub(r'\[Zum Artikel\]', '', content, flags=re.IGNORECASE)
    content = re.sub(r'\[.*?artikel.*?\]', '', content, flags=re.IGNORECASE)
    
    # 1. URLs zu klickbaren Links machen
    url_pattern = r'(https?://[^\s<>"]+)'
    content = re.sub(url_pattern, lambda m: _render_url(m.group(1)), content)
    
    # 2. Basic Telegram Markup
    # Fett: **text** oder __text__
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    content = re.sub(r'__(.*?)__', r'<strong>\1</strong>', content)
    
    # Kursiv: *text* oder _text_
    content = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', content)
    content = re.sub(r'(?<!_)_([^_]+?)_(?!_)', r'<em>\1</em>', content)
    
    # Code: `text`
    content = re.sub(r'`([^`]+?)`', r'<code>\1</code>', content)
    
    # 3. Zeilenumbrüche
    content = content.replace('\n', '<br>')
    
    # Entferne mehrfache Leerzeichen und leere Zeilen
    content = re.sub(r'<br>\s*<br>\s*<br>', '<br><br>', content)
    content = re.sub(r'^\s*<br>\s*', '', content)
    content = re.sub(r'\s*<br>\s*$', '', content)
    
    return Markup(content)


def regex_replace(content, pattern, replacement=''):
    """Regex replace filter for templates"""
    if not content:
        return ""
    return re.sub(pattern, replacement, content)


def _render_url(url):
    """
    Rendert URLs basierend auf ihrem Typ
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Bild-URLs
        if _is_image_url(url):
            return f'''
            <div class="telegram-image mt-2 mb-2">
                <img src="{url}" class="img-fluid rounded" 
                     style="max-width: 100%; max-height: 300px; object-fit: cover;"
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='block';"
                     loading="lazy">
                <div class="image-placeholder bg-light p-3 rounded text-center d-none">
                    <i class="bi bi-image text-muted fs-1"></i>
                    <div class="text-muted mt-2">
                        <small>Bild nicht verfügbar</small><br>
                        <a href="{url}" target="_blank" class="btn btn-sm btn-outline-primary mt-1">
                            <i class="bi bi-link-45deg"></i> Link öffnen
                        </a>
                    </div>
                </div>
            </div>
            '''
        
        # Video-URLs (YouTube, etc.)
        elif 'youtube.com' in domain or 'youtu.be' in domain:
            return f'''
            <div class="telegram-video mt-2 mb-2">
                <div class="bg-light p-3 rounded">
                    <i class="bi bi-play-circle text-primary fs-2"></i>
                    <div class="mt-2">
                        <strong>YouTube Video</strong><br>
                        <a href="{url}" target="_blank" class="btn btn-sm btn-primary mt-1">
                            <i class="bi bi-play"></i> Video ansehen
                        </a>
                    </div>
                </div>
            </div>
            '''
        
        # Normale Links
        else:
            domain_display = domain.replace('www.', '')
            return f'''
            <a href="{url}" target="_blank" class="telegram-link" 
               title="{url}">
                <i class="bi bi-link-45deg text-primary"></i> {domain_display}
            </a>
            '''
            
    except Exception:
        # Fallback für fehlerhafte URLs
        return f'<a href="{url}" target="_blank" class="telegram-link">{url}</a>'


def _is_image_url(url):
    """
    Prüft ob URL auf ein Bild zeigt
    """
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp')
    return any(url.lower().endswith(ext) for ext in image_extensions)


def clean_channel_name(channel):
    """Entfernt Telegram-Prefix von Kanalnamen"""
    if not channel:
        return ""
    
    # Entferne "Telegram" Prefix
    cleaned = re.sub(r'^Telegram\s*[-:]?\s*', '', channel, flags=re.IGNORECASE)
    
    return cleaned.strip()


def shorten_time_tag(time_str):
    """Kürzt Zeitangaben ab"""
    if not time_str:
        return ""
    
    # Mapping für Zeitkürzel
    time_mappings = {
        'last_hour': '1h',
        'last_6_hours': '6h',
        'hours_ago': 'h',
        'last_day': '1d',
        'days_ago': 'd',
        'last_week': '1w',
        'weeks_ago': 'w',
        'last_month': '1m',
        'months_ago': 'm',
        'last_year': '1y',
        'years_ago': 'y'
    }
    
    # Ersetze bekannte Zeitangaben
    for long_form, short_form in time_mappings.items():
        if long_form in time_str:
            return short_form
    
    # Fallback: Extrahiere Zahlen und Buchstaben
    match = re.search(r'(\d+)\s*(hour|day|week|month|year)', time_str, re.IGNORECASE)
    if match:
        number = match.group(1)
        unit = match.group(2)[0].lower()  # Erster Buchstabe
        return f"{number}{unit}"
    
    return time_str


def register_template_filters(app):
    """
    Registriert alle Template-Filter in der Flask-App
    """
    app.jinja_env.filters['render_telegram_content'] = render_telegram_content
    app.jinja_env.filters['render_telegram_content_clean'] = render_telegram_content_clean
    app.jinja_env.filters['regex_replace'] = regex_replace
    app.jinja_env.filters['get_link_previews'] = get_link_previews
    app.jinja_env.filters['clean_url_text'] = clean_url_text
    app.jinja_env.filters['clean_channel_name'] = clean_channel_name
    app.jinja_env.filters['shorten_time_tag'] = shorten_time_tag
