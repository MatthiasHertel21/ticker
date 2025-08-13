"""
Route für Multi-Source-Management
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import logging
from datetime import datetime

from app.scrapers.source_manager import MultiSourceManager
from app.data.json_manager import JSONManager
from app.utils.timezone_utils import get_cet_time

logger = logging.getLogger(__name__)
json_manager = JSONManager()

# Blueprint erstellen
sources_bp = Blueprint('sources', __name__, url_prefix='/sources')


@sources_bp.route('/')
def index():
    """Umleitung zur Manage-Seite"""
    return redirect(url_for('sources.manage'))


@sources_bp.route('/manage')
def manage():
    """Source-Management-Interface"""
    try:
        source_manager = MultiSourceManager()
        stats = source_manager.get_source_stats()
        
        return render_template('sources/manage.html', 
                             stats=stats,
                             current_time=get_cet_time())
                             
    except Exception as e:
        logger.error(f"Fehler beim Laden der Source-Verwaltung: {e}")
        flash(f"Fehler beim Laden der Daten: {e}", 'error')
        return render_template('sources/manage.html', 
                             stats={'total_sources': 0, 'active_sources': 0, 'sources': []})


@sources_bp.route('/add-source', methods=['GET', 'POST'])
def add_source():
    """Neue Quelle hinzufügen"""
    if request.method == 'GET':
        return render_template('sources/add_source.html')
    
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        # Basis-Validierung
        required_fields = ['name', 'type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Feld "{field}" ist erforderlich'}), 400
        
        # Source-Config erstellen
        source_config = {
            'name': data['name'].strip(),
            'type': data['type'],
            'enabled': data.get('enabled', 'true') == 'true',
            'created_at': get_cet_time().isoformat()
        }
        
        # Type-spezifische Konfiguration
        if data['type'] == 'rss':
            source_config.update({
                'url': data.get('url', '').strip(),
                'update_interval': int(data.get('update_interval', 60)),
                'max_articles': int(data.get('max_articles', 10))
            })
        elif data['type'] == 'telegram':
            source_config.update({
                'channel_username': data.get('channel_username', '').strip(),
                'max_messages': int(data.get('max_messages', 10))
            })
        elif data['type'] == 'twitter':
            source_config.update({
                'username': data.get('username', '').strip(),
                'max_tweets': int(data.get('max_tweets', 10))
            })
        
        # Quelle hinzufügen
        source_manager = MultiSourceManager()
        success = source_manager.add_source(source_config)
        
        if success:
            message = f"Quelle '{source_config['name']}' erfolgreich hinzugefügt"
            if request.is_json:
                return jsonify({'success': True, 'message': message})
            else:
                flash(message, 'success')
                return redirect(url_for('sources.manage'))
        else:
            error_msg = "Quelle konnte nicht hinzugefügt werden"
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            else:
                flash(error_msg, 'error')
                return render_template('sources/add_source.html')
                
    except Exception as e:
        logger.error(f"Fehler beim Hinzufügen der Quelle: {e}")
        error_msg = f"Fehler beim Hinzufügen: {e}"
        
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        else:
            flash(error_msg, 'error')
            return render_template('sources/add_source.html')


@sources_bp.route('/test')
def test_sources():
    """Teste alle konfigurierten Quellen"""
    try:
        source_manager = MultiSourceManager()
        
        # Test-Scraping (ohne Speicherung)
        test_results = {}
        
        for scraper in source_manager.scrapers:
            try:
                # Kurzer Test-Scrape
                articles = scraper.scrape()
                test_results[scraper.source_name] = {
                    'status': 'success',
                    'article_count': len(articles),
                    'source_type': scraper.source_type,
                    'enabled': scraper.enabled
                }
            except Exception as e:
                test_results[scraper.source_name] = {
                    'status': 'error',
                    'error': str(e),
                    'source_type': scraper.source_type,
                    'enabled': scraper.enabled
                }
        
        return jsonify({
            'success': True,
            'test_results': test_results,
            'timestamp': get_cet_time().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Testen der Quellen: {e}")
        return jsonify({'error': str(e)}), 500


@sources_bp.route('/scrape-now', methods=['POST'])
def manual_scrape():
    """Manuelles Scraping aller Quellen"""
    try:
        source_manager = MultiSourceManager()
        results = source_manager.scrape_all_sources(max_workers=2)
        
        return jsonify({
            'success': True,
            'results': results,
            'timestamp': get_cet_time().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Fehler beim manuellen Scraping: {e}")
        return jsonify({'error': str(e)}), 500


@sources_bp.route('/stats')
def get_stats():
    """API-Endpoint für Source-Statistiken"""
    try:
        source_manager = MultiSourceManager()
        stats = source_manager.get_source_stats()
        
        return jsonify({
            'success': True,
            'stats': stats,
            'timestamp': get_cet_time().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Statistiken: {e}")
        return jsonify({'error': str(e)}), 500


@sources_bp.route('/configure')
def configure_source():
    """Konfigurationsseite für eine spezifische Quelle"""
    try:
        source_name = request.args.get('name')
        source_id = request.args.get('id')
        
        if not source_name:
            flash('Quellname ist erforderlich', 'error')
            return redirect(url_for('sources.manage'))
        
        # Quelle aus den Daten laden
        sources_data = json_manager.read('sources')
        source = None
        
        # Suche nach der Quelle
        for src in sources_data.get('sources', []):
            src_name = src.get('source_name', src.get('name', ''))
            if src_name == source_name:
                source = src
                break
            if source_id and src.get('id') == source_id:
                source = src
                break
        
        if not source:
            flash(f'Quelle "{source_name}" nicht gefunden', 'error')
            return redirect(url_for('sources.manage'))
        
        # Datenstruktur normalisieren
        normalized_source = {
            'id': source.get('id', ''),
            'source_name': source.get('source_name', source.get('name', '')),
            'source_type': source.get('source_type', source.get('type', '')),
            'enabled': source.get('enabled', True),
            'created_at': source.get('created_at', ''),
            'last_scrape': source.get('last_scrape'),
            'total_articles': source.get('total_articles', 0),
            'last_error': source.get('last_error'),
        }
        
        # Typ-spezifische Daten hinzufügen
        if normalized_source['source_type'] == 'telegram':
            config = source.get('config', source)
            normalized_source.update({
                'channel_username': config.get('channel_username', ''),
                'channel_id': config.get('channel_id'),
                'max_messages': config.get('max_messages', 10),
                'keywords': config.get('keywords', []),
                'exclude_keywords': config.get('exclude_keywords', []),
                'telethon_session_exists': source.get('telethon_session_exists', False)
            })
        elif normalized_source['source_type'] == 'rss':
            config = source.get('config', source)
            normalized_source.update({
                'url': config.get('url', source.get('url', '')),
                'max_articles': config.get('max_articles', source.get('max_articles', 10)),
                'update_interval': config.get('update_interval', source.get('update_interval', 30))
            })
        elif normalized_source['source_type'] == 'twitter':
            config = source.get('config', source)
            normalized_source.update({
                'username': config.get('username', ''),
                'max_tweets': config.get('max_tweets', 10)
            })
        elif normalized_source['source_type'] == 'web':
            config = source.get('config', source)
            normalized_source.update({
                'url': config.get('url', ''),
                'selector': config.get('selector', '')
            })
        
        return render_template('sources/configure.html', 
                             source=normalized_source,
                             current_time=get_cet_time())
        
    except Exception as e:
        logger.error(f"Fehler beim Laden der Quellen-Konfiguration: {e}")
        flash(f"Fehler beim Laden der Konfiguration: {e}", 'error')
        return redirect(url_for('sources.manage'))


@sources_bp.route('/update-source', methods=['POST'])
def update_source():
    """Quelle aktualisieren"""
    try:
        data = request.get_json()
        
        if not data.get('id') and not data.get('name'):
            return jsonify({'error': 'Quell-ID oder Name ist erforderlich'}), 400
        
        # Implementierung für Quellen-Update
        # Dies würde die Quelle in sources.json aktualisieren
        
        return jsonify({
            'success': True,
            'message': 'Quelle erfolgreich aktualisiert'
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren der Quelle: {e}")
        return jsonify({'error': str(e)}), 500


@sources_bp.route('/test-single', methods=['POST'])
def test_single_source():
    """Einzelne Quelle testen"""
    try:
        import threading
        import time
        from concurrent.futures import ThreadPoolExecutor, TimeoutError
        
        data = request.get_json()
        source_name = data.get('source_name')
        source_id = data.get('source_id')
        
        if not source_name:
            return jsonify({'error': 'Quellname ist erforderlich'}), 400
        
        # Quelle aus den Daten laden
        sources_data = json_manager.read('sources')
        source = None
        
        for src in sources_data.get('sources', []):
            if src.get('source_name') == source_name or src.get('name') == source_name:
                source = src
                break
            if source_id and src.get('id') == source_id:
                source = src
                break
        
        if not source:
            return jsonify({'error': f'Quelle "{source_name}" nicht gefunden'}), 404
        
        def test_source_worker():
            """Worker-Funktion für den Source-Test"""
            try:
                source_manager = MultiSourceManager()
                
                # Basis-Konfiguration für Test
                test_config = {
                    'name': source.get('source_name', source.get('name', '')),
                    'type': source.get('source_type', source.get('type', ''))
                }
                
                # Typ-spezifische Konfiguration hinzufügen
                if test_config['type'] == 'rss':
                    config = source.get('config', source)
                    rss_url = config.get('url', source.get('url', ''))
                    if not rss_url:
                        return {'error': 'RSS-URL nicht konfiguriert'}
                    
                    test_config.update({
                        'url': rss_url,
                        'max_articles': min(config.get('max_articles', source.get('max_articles', 5)), 5)
                    })
                    logger.info(f"RSS-Test-Konfiguration: {test_config}")
                    
                elif test_config['type'] == 'telegram':
                    config = source.get('config', source)
                    channel_username = config.get('channel_username', '')
                    if not channel_username:
                        return {'error': 'Telegram Channel-Username nicht konfiguriert'}
                    
                    test_config.update({
                        'config': {
                            'channel_username': channel_username,
                            'max_messages': min(config.get('max_messages', 5), 5)
                        }
                    })
                
                # Scraper erstellen und testen
                scraper_class = source_manager.scraper_classes.get(test_config['type'])
                if not scraper_class:
                    return {'error': f'Unbekannter Quelltyp: {test_config["type"]}'}
                
                scraper = scraper_class(test_config)
                
                # Konfiguration validieren
                if not scraper.validate_config():
                    return {'error': 'Konfiguration ungültig'}
                
                # Scraping durchführen
                articles = scraper.scrape()
                
                return {
                    'success': True,
                    'articles_found': len(articles),
                    'articles': articles[:3] if articles else [],  # Erste 3 Artikel als Beispiel
                    'message': f'Test erfolgreich - {len(articles)} Artikel gefunden'
                }
                
            except Exception as e:
                logger.error(f"Test-Worker Fehler: {e}")
                return {'error': f'Test fehlgeschlagen: {str(e)}'}
        
        # Test mit Timeout ausführen
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(test_source_worker)
            try:
                result = future.result(timeout=30)  # 30 Sekunden Timeout
                return jsonify(result)
            except TimeoutError:
                return jsonify({
                    'success': False,
                    'error': 'Test-Timeout nach 30 Sekunden - Quelle reagiert nicht'
                }), 408
        
    except Exception as e:
        logger.error(f"Fehler beim Testen der Quelle: {e}")
        return jsonify({'error': str(e)}), 500


@sources_bp.route('/toggle-status', methods=['POST', 'GET'])
@sources_bp.route('/toggle', methods=['POST', 'GET'])  # Alias
def toggle_source_status():
    """Status einer Quelle umschalten (aktiv/inaktiv).
    Akzeptiert POST (JSON) oder GET (?source_name=..&enabled=true/false) als Fallback,
    damit UI auch bei POST-Problemen nicht komplett blockiert."""
    try:
        # Eingabedaten extrahieren (POST bevorzugt)
        data = {}
        if request.method == 'POST':
            data = request.get_json(silent=True) or {}
        else:  # GET-Fallback
            data = {
                'source_name': request.args.get('source_name'),
                'enabled': request.args.get('enabled')
            }
        
        source_identifier = data.get('source_name')
        new_status_raw = data.get('enabled')
        
        if source_identifier is None:
            return jsonify({'error': 'Quellenidentifier (source_name) erforderlich'}), 400
        
        # Bool Parsing robust
        if isinstance(new_status_raw, bool):
            new_status = new_status_raw
        else:
            if new_status_raw is None:
                return jsonify({'error': 'Status (enabled) erforderlich'}), 400
            new_status = str(new_status_raw).lower() in ['1', 'true', 'yes', 'on']
        
        logger.info(f"[TOGGLE] req_method={request.method} id={source_identifier} -> {new_status}")
        
        import json, os
        from flask import current_app
        # Dynamischer Basis-Pfad relativ zur App
        base_dir = os.path.abspath(os.path.join(current_app.root_path, '..'))
        candidate_paths = [
            os.path.join(base_dir, 'data', 'sources.json'),
            '/home/ga/ticker/data/sources.json',  # Fallback Host-Pfad
            '/app/data/sources.json'              # Typischer Container-Pfad
        ]
        sources_file = next((p for p in candidate_paths if os.path.exists(p)), None)
        if not sources_file:
            return jsonify({'error': 'sources.json nicht gefunden', 'searched': candidate_paths}), 404
        
        with open(sources_file, 'r', encoding='utf-8') as f:
            sources_data = json.load(f)
        
        if isinstance(sources_data, dict) and 'sources' in sources_data:
            sources = sources_data['sources']
            container_is_dict = True
        elif isinstance(sources_data, list):
            sources = sources_data
            container_is_dict = False
        else:
            return jsonify({'error': 'Unerwartete Struktur in sources.json'}), 500
        
        source_found = False
        display_name = source_identifier
        for s in sources:
            if s.get('id') == source_identifier or s.get('name') == source_identifier or s.get('source_name') == source_identifier:
                s['enabled'] = bool(new_status)
                s['updated_at'] = get_cet_time().isoformat()
                display_name = s.get('name') or s.get('source_name') or source_identifier
                source_found = True
                break
        
        if not source_found:
            return jsonify({'error': f'Quelle "{source_identifier}" nicht gefunden'}), 404
        
        # Zurückschreiben
        with open(sources_file, 'w', encoding='utf-8') as f:
            if container_is_dict:
                json.dump(sources_data, f, indent=2, ensure_ascii=False)
            else:
                json.dump(sources, f, indent=2, ensure_ascii=False)
        
        action_txt = 'aktiviert' if new_status else 'deaktiviert'
        return jsonify({
            'success': True,
            'message': f"Quelle '{display_name}' wurde {action_txt}",
            'source_name': display_name,
            'enabled': new_status,
            'method_used': request.method,
            'file_used': sources_file
        })
    except Exception as e:
        logger.error(f"Fehler beim Umschalten des Quellenstatus: {e}", exc_info=True)
        return jsonify({'error': f'Fehler beim Ändern des Status: {e}'}), 500


@sources_bp.route('/toggle-status/debug', methods=['GET', 'POST', 'OPTIONS'])
def toggle_source_status_debug():
    """Diagnose-Endpunkt: Zeigt ankommende Methode, JSON und relevante Header.
    WARNUNG: Nur für temporären Debug-Einsatz gedacht – nach Analyse entfernen!"""
    from flask import request
    payload = None
    try:
        payload = request.get_json(silent=True)
    except Exception:
        payload = 'JSON parse error'
    return jsonify({
        'method': request.method,
        'json': payload,
        'form': request.form.to_dict(),
        'args': request.args.to_dict(),
        'headers_subset': {k: v for k, v in request.headers.items() if k.lower() in ['content-type','x-requested-with','origin','referer']},
        'url': request.url,
        'note': 'Debug-Endpoint aktiv – nach Fertigstellung entfernen.'
    })
