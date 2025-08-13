"""
Telegram-Management Routes
"""

from flask import Blueprint, request, jsonify, render_template, send_file
from app.data import json_manager
try:
    from app.scrapers import TelegramChannelMonitor
except ImportError:
    TelegramChannelMonitor = None
import asyncio
import os
import logging
import io

bp = Blueprint('telegram', __name__, url_prefix='/telegram')
logger = logging.getLogger(__name__)


@bp.route('/api/telegram-media/<media_id>')
def get_telegram_media(media_id):
    """API endpoint to serve Telegram media"""
    try:
        from app.data import json_manager
        import os
        
        # Suche lokal gespeicherte Datei
        articles = json_manager.read('articles')
        for article in articles.get('articles', []):
            if article.get('media') and article['media'].get('images'):
                for img in article['media']['images']:
                    if img.get('id') == media_id and img.get('type') == 'telegram_photo':
                        # Prüfe ob lokale Datei existiert
                        if img.get('filename'):
                            local_path = f"/app/data/media/{img['filename']}"
                            docker_path = f"/home/ga/ticker/data/media/{img['filename']}"
                            
                            # Prüfe beide Pfade (Container und Host)
                            if os.path.exists(local_path):
                                return send_file(local_path, mimetype='image/jpeg')
                            elif os.path.exists(docker_path):
                                return send_file(docker_path, mimetype='image/jpeg')
        
        # Fallback: Versuche Download von Telegram
        from app.scrapers.telethon_scraper import download_telegram_media
        media_data = download_telegram_media(media_id)
        
        if not media_data:
            return jsonify({'error': 'Media not found'}), 404
        
        return send_file(io.BytesIO(media_data), mimetype='image/jpeg')
        
    except Exception as e:
        logger.error(f"Error serving media {media_id}: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/media/<filename>')
def serve_media(filename):
    """Serve local media files"""
    try:
        import os
        from flask import send_from_directory
        
        # Sicherheitsprüfung: nur erlaubte Dateierweiterungen
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Versuche Container-Pfad zuerst
        container_path = "/app/data/media"
        host_path = "/home/ga/ticker/data/media"
        
        if os.path.exists(os.path.join(container_path, filename)):
            return send_from_directory(container_path, filename)
        elif os.path.exists(os.path.join(host_path, filename)):
            return send_from_directory(host_path, filename)
        else:
            return jsonify({'error': 'File not found'}), 404
            
    except Exception as e:
        logger.error(f"Error serving file {filename}: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/')
def telegram_dashboard():
    """Telegram-Dashboard"""
    sources = json_manager.read('sources')
    sources_list = sources.get('sources', [])
    
    # Filter für Telegram-Quellen - unterstützt sowohl alte (dict) als auch neue (list) Struktur
    if isinstance(sources_list, list):
        # Neue Struktur: Liste von Quellen-Objekten
        telegram_sources = {
            source.get('name', f'source_{i}'): source 
            for i, source in enumerate(sources_list) 
            if source.get('type') == 'telegram'
        }
    else:
        # Alte Struktur: Dictionary mit Quellen
        telegram_sources = {k: v for k, v in sources_list.items() 
                           if v.get('type') == 'telegram'}
    
    return render_template('telegram.html', channels=telegram_sources)


@bp.route('/add-channel', methods=['POST'])
def add_channel():
    """Füge neuen Telegram-Channel hinzu"""
    try:
        data = request.get_json()
        channel_username = data.get('channel_username', '').strip()
        keywords = data.get('keywords', [])
        exclude_keywords = data.get('exclude_keywords', [])
        
        if not channel_username:
            return jsonify({'success': False, 'error': 'Channel Username erforderlich'})
        
        # Bot-Token prüfen
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            return jsonify({'success': False, 'error': 'Telegram Bot Token nicht konfiguriert'})
        
        # Channel hinzufügen
        monitor = TelegramChannelMonitor(bot_token)
        
        # Async-Funktion in sync-Context ausführen
        async def add_channel_async():
            return await monitor.add_channel(channel_username, keywords, exclude_keywords)
        
        source_id = asyncio.run(add_channel_async())
        
        return jsonify({
            'success': True,
            'source_id': source_id,
            'message': f'Channel @{channel_username} hinzugefügt'
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Hinzufügen von Channel: {e}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/remove-channel/<source_id>', methods=['DELETE'])
def remove_channel(source_id):
    """Entferne Telegram-Channel"""
    try:
        json_manager.delete_item('sources', source_id)
        return jsonify({'success': True, 'message': 'Channel entfernt'})
    except Exception as e:
        logger.error(f"Fehler beim Entfernen von Channel {source_id}: {e}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/edit-channel/<source_id>', methods=['POST'])
def edit_channel(source_id):
    """Bearbeite Telegram-Channel"""
    try:
        from app.scrapers.source_manager import MultiSourceManager
        
        data = request.form
        source_manager = MultiSourceManager()
        
        # Channel-Daten aktualisieren
        update_data = {
            'name': data.get('name'),
            'enabled': 'enabled' in data,
            'config': {
                'channel_username': data.get('channel_username'),
                'keywords': [k.strip() for k in data.get('keywords', '').split(',') if k.strip()],
                'exclude_keywords': [k.strip() for k in data.get('exclude_keywords', '').split(',') if k.strip()]
            }
        }
        
        # Source aktualisieren
        source_manager.update_source(source_id, update_data)
        
        return jsonify({'success': True, 'message': 'Channel aktualisiert'})
    except Exception as e:
        logger.error(f"Fehler beim Bearbeiten von Channel {source_id}: {e}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/delete-channel/<source_id>', methods=['POST'])
def delete_channel(source_id):
    """Lösche Telegram-Channel"""
    try:
        from app.scrapers.source_manager import MultiSourceManager
        
        source_manager = MultiSourceManager()
        source_manager.remove_source(source_id)
        
        return jsonify({'success': True, 'message': 'Channel gelöscht'})
    except Exception as e:
        logger.error(f"Fehler beim Löschen von Channel {source_id}: {e}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/telethon/setup', methods=['GET', 'POST'])
def telethon_setup():
    """Setup-Interface für Telethon"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            api_id = data.get('api_id')
            api_hash = data.get('api_hash')
            phone = data.get('phone')
            
            if not all([api_id, api_hash, phone]):
                return jsonify({
                    'success': False,
                    'error': 'Alle Felder sind erforderlich'
                }), 400
            
            logger.info(f"Telethon Setup mit API_ID: {api_id}, Phone: {phone[:8]}...")
            
            # Starte Authentifizierung
            from app.scrapers.telethon_scraper import sync_start_telethon_auth
            result = sync_start_telethon_auth(api_id, api_hash, phone)
            
            if result['success']:
                if result.get('already_authorized'):
                    return jsonify({
                        'success': True,
                        'already_authorized': True,
                        'message': 'Telethon ist bereits authentifiziert!'
                    })
                elif result.get('code_sent'):
                    return jsonify({
                        'success': True,
                        'code_sent': True,
                        'message': 'SMS-Code wurde gesendet. Bitte gib den Code ein.',
                        'phone': phone
                    })
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Unbekannter Fehler')
                }), 500
            
        except Exception as e:
            logger.error(f"Fehler beim Telethon-Setup: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # GET-Request: Setup-Seite anzeigen mit vorausgefüllten Werten
    api_id = os.getenv('TELEGRAM_API_ID', '')
    api_hash = os.getenv('TELEGRAM_API_HASH', '')
    phone = os.getenv('TELEGRAM_PHONE', '')
    
    # Prüfe ob bereits authentifiziert
    is_authenticated = False
    user_name = None
    
    try:
        if api_id and api_hash:
            # Einfache Session-Datei-Prüfung ohne Event Loop
            session_file = '/app/data/telethon_session.session'
            if os.path.exists(session_file) and os.path.getsize(session_file) > 0:
                is_authenticated = True
                logger.info("Telethon Session-Datei gefunden")
    except Exception as e:
        logger.debug(f"Auth-Check fehlgeschlagen: {e}")
    
    return render_template('telethon_setup.html', 
                         api_id=api_id, 
                         api_hash=api_hash, 
                         phone=phone,
                         is_authenticated=is_authenticated,
                         user_name=user_name)


@bp.route('/telethon/verify', methods=['POST'])
def telethon_verify():
    """Verifizierung des Telegram-Codes"""
    try:
        data = request.get_json()
        verification_code = data.get('code')
        phone = data.get('phone')
        password = data.get('password')  # Für 2FA
        
        if not verification_code or not phone:
            return jsonify({
                'success': False,
                'error': 'Verifikationscode und Telefonnummer sind erforderlich'
            }), 400
        
        logger.info(f"Verifikation für {phone[:8]}... mit Code: {verification_code[:3]}...")
        
        # Authentifizierung abschließen
        from app.scrapers.telethon_scraper import sync_complete_telethon_auth
        result = sync_complete_telethon_auth(phone, verification_code, password)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': f"Telegram-Account erfolgreich verifiziert als {result.get('user', 'Benutzer')}",
                'status': 'authenticated',
                'user': result.get('user')
            })
        elif result.get('error') == 'two_factor_required':
            return jsonify({
                'success': False,
                'error': 'two_factor_required',
                'message': result.get('message', 'Zwei-Faktor-Authentifizierung erforderlich')
            }), 202  # Accepted, but needs additional input
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Verifikation fehlgeschlagen')
            }), 400
        
    except Exception as e:
        logger.error(f"Fehler bei der Telethon-Verifikation: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/telethon/scrape', methods=['POST'])
def telethon_scrape():
    """Startet Telethon-basiertes Scraping"""
    try:
        # Prüfe ob Telethon konfiguriert ist
        api_id = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        
        if not all([api_id, api_hash]):
            return jsonify({
                'success': False,
                'error': 'Telethon ist noch nicht konfiguriert',
                'setup_required': True
            }), 400
        
        # Echtes Telethon-Scraping starten (mit mehr Nachrichten für letzte Stunde)
        from app.scrapers.telethon_scraper import sync_scrape_telegram_telethon
        
        logger.info("Starte Telethon-Scraping (20 Kanäle × 20 Nachrichten + Duplikatsschutz)...")
        new_articles = sync_scrape_telegram_telethon(limit=20)  # 20 pro Kanal
        
        return jsonify({
            'success': True,
            'message': f'Telethon-Scraping abgeschlossen: {new_articles} neue Artikel',
            'new_articles': new_articles
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Telethon-Scraping: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/test-bot', methods=['GET'])
def test_bot():
    """Teste Telegram Bot-Verbindung"""
    try:
        from config.config import Config
        from app.scrapers.telegram_bot import TelegramChannelMonitor
        
        # Hole Bot Token aus Config
        bot_token = getattr(Config, 'TELEGRAM_BOT_TOKEN', None)
        
        if not bot_token:
            return jsonify({
                'success': False,
                'error': 'Telegram Bot Token nicht konfiguriert. Bitte TELEGRAM_BOT_TOKEN in Umgebungsvariablen setzen.'
            })
        
        # Erstelle Monitor und teste Verbindung
        monitor = TelegramChannelMonitor(bot_token)
        
        # Einfacher Test: Versuche Bot-Info abzurufen
        async def test_bot_connection():
            try:
                bot_info = await monitor.bot.get_me()
                return bot_info
            except Exception as e:
                raise e
        
        # Führe Test aus mit Event Loop Handling
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Wenn bereits ein Event Loop läuft, nutze Thread-Pool
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, test_bot_connection())
                    bot_info = future.result(timeout=10)
            else:
                bot_info = asyncio.run(test_bot_connection())
        except RuntimeError:
            # Fallback wenn kein Event Loop verfügbar
            bot_info = asyncio.run(test_bot_connection())
        
        if bot_info:
            return jsonify({
                'success': True,
                'bot_info': f"Bot @{bot_info.username} ({bot_info.first_name})",
                'message': 'Bot-Verbindung erfolgreich'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Bot-Verbindung fehlgeschlagen - keine Bot-Info erhalten'
            })
            
    except Exception as e:
        logger.error(f"Bot-Test fehlgeschlagen: {e}")
        return jsonify({
            'success': False,
            'error': f'Bot-Test Fehler: {str(e)}'
        })


@bp.route('/manual-sync', methods=['POST'])
def manual_sync():
    """Manueller Sync aller Telegram-Channels"""
    try:
        from app.scrapers import sync_monitor_telegram_channels
        
        new_articles = sync_monitor_telegram_channels()
        
        return jsonify({
            'success': True,
            'new_articles': new_articles,
            'message': f'{new_articles} neue Artikel gesammelt'
        })
        
    except Exception as e:
        logger.error(f"Manueller Sync fehlgeschlagen: {e}")
        return jsonify({'success': False, 'error': str(e)})
