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
    # URLs in Text zu Links machen – aber NICHT solche direkt in href="..."
    url_pattern = r'(?<!href=")(?!")(?<!href=\')(https?://[^\s<>"\']+)'  # negative lookbehind auf href=" oder href='
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
            return (
                f"<div class='telegram-image mt-2 mb-2'>"
                f"<img src='{url}' class='img-fluid rounded' style='max-width:100%;max-height:300px;object-fit:cover;' "
                f"onerror=\"this.style.display='none';this.nextElementSibling.style.display='block';\" loading='lazy'>"
                f"<div class='image-placeholder bg-light p-3 rounded text-center d-none'>"
                f"<i class='bi bi-image text-muted fs-1'></i>"
                f"<div class='text-muted mt-2'><small>Bild nicht verfügbar</small><br>"
                f"<a href='{url}' target='_blank' class='btn btn-sm btn-outline-primary mt-1'><i class='bi bi-link-45deg'></i> Link öffnen</a>"
                f"</div></div></div>"
            )
        # Video-URLs
        if 'youtube.com' in domain or 'youtu.be' in domain:
            return (
                f"<div class='telegram-video mt-2 mb-2'><div class='bg-light p-3 rounded'>"
                f"<i class='bi bi-play-circle text-primary fs-2'></i>"
                f"<div class='mt-2'><strong>YouTube Video</strong><br>"
                f"<a href='{url}' target='_blank' class='btn btn-sm btn-primary mt-1'><i class='bi bi-play'></i> Video ansehen</a>"
                f"</div></div></div>"
            )
        # Standard-Link
        domain_display = domain.replace('www.', '')
        return (f"<a href='{url}' target='_blank' class='telegram-link' title='{url}'>"
                f"<i class='bi bi-link-45deg text-primary'></i> {domain_display}</a>")
            
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
    app.jinja_env.filters['truncate_words_media'] = truncate_words_media
    app.jinja_env.filters['truncate_chars_media'] = truncate_chars_media
    app.jinja_env.filters['sanitize_full_html'] = sanitize_full_html


def truncate_words_media(html_content: str, max_words: int = 300, max_images: int = 1):
    """Nicht-destruktive Kürzung: behält Struktur, limitiert Wörter & Bilder.
    Entfernt überzählige Bilder vollständig und kappt nach max_words, ohne Tags zu zerbrechen.
    Gibt dict {html, truncated} zurück."""
    if not html_content:
        return {'html': '', 'truncated': False}
    try:
        from bs4 import BeautifulSoup, NavigableString, Tag
    except ImportError:
        words_simple = html_content.split()
        truncated = len(words_simple) > max_words
        return {'html': ' '.join(words_simple[:max_words]) + (' …' if truncated else ''), 'truncated': truncated}

    soup = BeautifulSoup(str(html_content), 'html.parser')

    # Entferne offensichtliche Attribut-/Tag-Artefakte die als nackter Text herumliegen
    artefact_regex = re.compile(r'^"?(style|width|height|class|loading|onerror)=\"[^\"]*\"/?>?$')
    stray_quote_regex = re.compile(r'^"\s*$')
    for tn in list(soup.find_all(string=True)):
        s = tn.strip()
        if not s:
            continue
        if artefact_regex.match(s) or stray_quote_regex.match(s) or s in {"/>", ">"}:
            tn.extract()

    # Bild-Wrapper (unsere generierten div.telegram-image) begrenzen
    image_wrappers = soup.select('div.telegram-image')
    images_truncated = False
    for idx, wrapper in enumerate(image_wrappers):
        if idx >= max_images:
            wrapper.decompose()
            images_truncated = True

    # Wortanzahl vor Kürzung bestimmen
    # Normalisierten Text für solide Wortanzahl (mehrfache Leerzeichen -> eins)
    normalized_text = re.sub(r'\s+', ' ', soup.get_text(' ').strip())
    total_words = len(re.findall(r'\S+', normalized_text))
    if total_words <= max_words and not images_truncated:
        # Keine Kürzung notwendig
        html_out = str(soup)
        html_out = re.sub(r'(?:<br\s*/?>\s*){3,}', '<br><br>', html_out)
        html_out = re.sub(r'\s+</', '</', html_out)
        return {'html': html_out, 'truncated': False}

    # Kürzen auf max_words
    remaining = max_words
    for node in list(soup.descendants):
        if remaining <= 0:
            # Rest entfernen
            if hasattr(node, 'extract'):
                try:
                    node.extract()
                except Exception:
                    pass
            continue
        if isinstance(node, NavigableString):
            txt = str(node)
            # Reduziere Mehrfach-Whitespace im Textknoten lokal um saubere Zählung zu sichern
            txt_compact = re.sub(r'\s+', ' ', txt)
            words = re.findall(r'\S+', txt_compact)
            if not words:
                continue
            if len(words) <= remaining:
                remaining -= len(words)
            else:
                # Teil behalten
                keep = words[:remaining]
                node.replace_with(' '.join(keep) + ' …')
                remaining = 0
        # Wenn remaining 0 wird, weitere Knoten später entfernt (oben am Schleifenanfang)

    # Nachträglich alle vollständig leeren Tags ohne Inhalte entfernen
    for tag in list(soup.find_all()):
        if tag.name not in ('img','br') and not tag.get_text(strip=True) and not tag.find('img'):
            tag.decompose()

    html_out = str(soup)
    # Entferne führende/trailing <br>
    html_out = re.sub(r'^(?:\s*<br\s*/?>\s*)+', '', html_out)
    html_out = re.sub(r'(?:\s*<br\s*/?>\s*)+$', '', html_out)
    # Kollabiere >2 <br> zu genau 2, dann >1 leere Zeilen in Text zu 1
    html_out = re.sub(r'(?:<br\s*/?>\s*){3,}', '<br><br>', html_out)
    html_out = re.sub(r'(?:\n\s*){3,}', '\n\n', html_out)
    # Mehrfach-Leerzeichen zwischen Tags reduzieren
    html_out = re.sub(r'>\s{2,}<', '><', html_out)
    html_out = re.sub(r'\s+</', '</', html_out)
    return {'html': html_out, 'truncated': True}


def truncate_chars_media(html_content: str, max_chars: int = 640, max_images: int = 1):
    """Kürzerer Preview-Filter: max_chars Zeichen (Plaintext) (Standard jetzt 640) + max_images Bilder.
    Entfernt leere/kaputte Images, HTML-Fragmente und kollabiert mehrfachen Zeilenabstand auf einen.
    Liefert dict {html, truncated}."""
    if not html_content:
        return {'html': '', 'truncated': False}
    try:
        from bs4 import BeautifulSoup, NavigableString, Tag
    except ImportError:
        text = re.sub(r'\s+', ' ', html_content).strip()
        truncated = len(text) > max_chars
        return {'html': (text[:max_chars] + ' …') if truncated else text, 'truncated': truncated}

    soup = BeautifulSoup(str(html_content), 'html.parser')

    # Entferne kaputte / Escaped-Class Fragmente (rss<em>texte, spip</em>out etc.)
    for tag in soup.find_all(True):
        cls = tag.get('class')
        if cls:
            cleaned_classes = []
            for c in cls:
                if '<' in c or '>' in c or '/' in c:
                    continue
                cleaned_classes.append(c)
            if cleaned_classes:
                tag['class'] = cleaned_classes
            else:
                del tag['class']
    # Artefakt-Strings entfernen (z.B. " width="1029" /> / style="...")
    # Artefakt-Pattern: einzelne oder mehrere nackte Attribut-Fragmente (style="..." width="123" ... />)
    artefact_pattern = re.compile(r'^"?\s*(?:[a-zA-Z:-]+\s*=\s*"[^"]*"\s*){1,8}/?>?$')
    for tn in list(soup.find_all(string=True)):
        raw = tn.strip()
        if not raw:
            continue
        if artefact_pattern.match(raw):
            tn.extract()

    # Listelemente in Plaintext konvertieren / entfernen: <li> -> Inhalt + <br>; Wrapper <ul>/<ol> entfernen
    for li in list(soup.find_all('li')):
        text = li.get_text(' ', strip=True)
        li.replace_with(soup.new_string(text + '\n'))
    for wrapper in list(soup.find_all(['ul', 'ol'])):
        wrapper.unwrap()

    # Leere/img ohne src oder src sehr kurz entfernen, sowie überzählige Bilder
    imgs = soup.find_all('img')
    kept = 0
    for img in list(imgs):
        src = img.get('src','')
        if not src or len(src.strip()) < 5:
            img.decompose()
            continue
        kept += 1
        if kept > max_images:
            img.decompose()

    # Mehrfache <br> direkt nach Bildentfernung bereinigen (strukturorientiert)
    last_was_br = False
    for br in list(soup.find_all('br')):
        if last_was_br:
            br.decompose()
            continue
        last_was_br = True
        # Wenn nächstes kein <br>, reset folgt automatisch
        nxt = br.next_sibling
        if not (getattr(nxt, 'name', None) == 'br' or (isinstance(nxt, str) and not nxt.strip())):
            last_was_br = False

    # Plaintext sammeln für Zeichenlimit; wir bauen beim Traversieren ab
    collected = 0
    truncated = False
    for node in list(soup.descendants):
        if isinstance(node, NavigableString):
            txt = str(node)
            # Normalisiere Whitespace lokal
            norm = re.sub(r'\s+', ' ', txt)
            if not norm.strip():
                # neutrale Whitespaces behalten (kürzen später) – lassen stehen
                continue
            remaining = max_chars - collected
            if remaining <= 0:
                node.extract()
                truncated = True
                continue
            if len(norm) <= remaining:
                collected += len(norm)
                # Ersetze den Textknoten durch normalisierte Variante (verhindert Fragment-Artefakte)
                if norm != txt:
                    node.replace_with(norm)
            else:
                # Teile abschneiden
                piece = norm[:remaining] + ' …'
                node.replace_with(piece)
                collected += remaining
                truncated = True
        elif isinstance(node, Tag) and node.name == 'br':
            # br zählt nicht in Zeichenlimit ein
            continue

    # Nachbearbeitung: Mehrfache <br>/<p> Leerzeilen auf eine reduzieren
    html_out = str(soup)
    # Leere Formatierungstags (<strong></strong>, <i></i>, <em></em>) raus
    html_out = re.sub(r'<(strong|b|i|em|code)\b[^>]*>\s*</\1>', '', html_out)
    # Führende/trailing whitespace & <br>
    html_out = re.sub(r'^(?:\s|<br\s*/?>)+', '', html_out)
    html_out = re.sub(r'(?:\s|<br\s*/?>)+$', '', html_out)
    # Mehrfach <br> -> ein <br> (iterativ bis wirklich keine Ketten mehr)
    while re.search(r'(?:<br\s*/?>\s*){2,}', html_out):
        html_out = re.sub(r'(?:<br\s*/?>\s*){2,}', '<br>', html_out)
    # Mehrere leere Zeilen (auch mit &nbsp;) -> eine
    html_out = re.sub(r'(?:\n|\r|&nbsp;|\s){2,}', ' ', html_out)
    # Entferne doppelte Spaces
    html_out = re.sub(r' {2,}', ' ', html_out)
    # Doppelspacen zwischen Tags entfernen
    html_out = re.sub(r'>\s{2,}<', '><', html_out)
    # Überflüssige Spaces vor schließenden Tags
    html_out = re.sub(r'\s+</', '</', html_out)

    # Redundante Breaks zwischen Paragraphen entfernen (</p><br><p ... -> </p><p ...)
    html_out = re.sub(r'</p>\s*(?:<br\s*/?>\s*)+<p', '</p><p', html_out, flags=re.IGNORECASE)
    # Einzelne </p><br/> Sequenz vereinfachen
    html_out = re.sub(r'</p>\s*<br\s*/?>', '</p>', html_out, flags=re.IGNORECASE)
    # Einzelne <br/><p Sequenz vereinfachen
    html_out = re.sub(r'<br\s*/?>\s*<p', '<p', html_out, flags=re.IGNORECASE)
    # Leere Paragraphen vollständig entfernen (auch wenn nur <br> darin)
    html_out = re.sub(r'<p\b[^>]*>\s*(?:<br\s*/?>\s*)*</p>', '', html_out, flags=re.IGNORECASE)
    return {'html': html_out, 'truncated': truncated}


def sanitize_full_html(html_content: str):
    """Sanitizes full (ungetrimmter) Inhalt: entfernt leere Paragraphen, überflüssige <br>, Artefakt-Fragmente, defekte Klassen.
    Schneidet NICHT Text oder Bilder (außer kaputten/ohne src)."""
    if not html_content:
        return ''
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        # Minimal Fallback: reduziere mehrfach <br>
        return re.sub(r'(?:<br\s*/?>\s*){2,}', '<br>', html_content)

    soup = BeautifulSoup(str(html_content), 'html.parser')

    # Entferne kaputte Klassenfragmente
    for tag in soup.find_all(True):
        cls = tag.get('class')
        if cls:
            cleaned = [c for c in cls if '<' not in c and '>' not in c and '/' not in c]
            if cleaned:
                tag['class'] = cleaned
            else:
                del tag['class']

    # Kaputte / leere Images
    for img in list(soup.find_all('img')):
        src = img.get('src','')
        if not src or len(src.strip()) < 5:
            img.decompose()

    # Listenelemente entfernen / in Zeilen umwandeln (wie in truncate):
    for li in list(soup.find_all('li')):
        text = li.get_text(' ', strip=True)
        li.replace_with(soup.new_string(text + '\n'))
    for wrapper in list(soup.find_all(['ul','ol'])):
        wrapper.unwrap()

    # Entferne lose Attribut-Bundle Fragmente als Textknoten (wie im truncate Filter)
    attribute_bundle_pattern = re.compile(r'^"?\s*(?:[a-zA-Z:-]+\s*=\s*"[^"]*"\s*){1,8}/?>?$')
    for tn in list(soup.find_all(string=True)):
        raw = tn.strip()
        if not raw:
            continue
        if attribute_bundle_pattern.match(raw):
            tn.extract()

    # Leere Formatierungstags
    for selector in ['strong','b','i','em','code']:
        for t in list(soup.find_all(selector)):
            if not t.get_text(strip=True):
                t.decompose()

    # Redundante br Sequenzen strukturell reduzieren
    last_was_br = False
    for br in list(soup.find_all('br')):
        if last_was_br:
            br.decompose()
            continue
        last_was_br = True
        nxt = br.next_sibling
        if not (getattr(nxt,'name',None) == 'br' or (isinstance(nxt,str) and not str(nxt).strip())):
            last_was_br = False

    html_out = str(soup)
    # Patternbereinigung wie beim truncate
    html_out = re.sub(r'</p>\s*(?:<br\s*/?>\s*)+<p', '</p><p', html_out, flags=re.IGNORECASE)
    html_out = re.sub(r'</p>\s*<br\s*/?>', '</p>', html_out, flags=re.IGNORECASE)
    html_out = re.sub(r'<br\s*/?>\s*<p', '<p', html_out, flags=re.IGNORECASE)
    html_out = re.sub(r'<p\b[^>]*>\s*(?:<br\s*/?>\s*)*</p>', '', html_out, flags=re.IGNORECASE)
    # Iterativ Mehrfach <br>
    while re.search(r'(?:<br\s*/?>\s*){2,}', html_out):
        html_out = re.sub(r'(?:<br\s*/?>\s*){2,}', '<br>', html_out)
    # Whitespace säubern
    html_out = re.sub(r'>\s+<', '><', html_out)
    # Entferne defekte style-Attribute Fragmente (style="/> oder style=" />)
    html_out = re.sub(r'style="\s*/?>', '', html_out)
    html_out = re.sub(r'style="\s*"\s*/?>', '', html_out)
    # Entferne übrig gebliebene reine Attribut-Bündel Texte (z.B. " style="..." width="123" />) falls doch als Text vorhanden
    html_out = re.sub(r'>"?\s*(?:[a-zA-Z:-]+\s*=\s*"[^"]*"\s*){1,8}/?>', '>', html_out)
    # Leere <li></li> die eventuell übrig blieben
    html_out = re.sub(r'<li\b[^>]*>\s*</li>', '', html_out, flags=re.IGNORECASE)
    return html_out
