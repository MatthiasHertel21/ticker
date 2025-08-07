"""
Telegram-Management Routes
"""

from flask import Blueprint, request, jsonify, render_template
from app.data import json_manager
from app.scrapers import TelegramChannelMonitor
import asyncio
import os
import logging

bp = Blueprint('telegram', __name__, url_prefix='/telegram')
logger = logging.getLogger(__name__)


@bp.route('/')
def telegram_dashboard():
    """Telegram-Dashboard"""
    sources = json_manager.read('sources')
    telegram_sources = {k: v for k, v in sources.get('sources', {}).items() 
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


@bp.route('/test-bot')
def test_bot():
    """Teste Telegram-Bot-Verbindung"""
    try:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            return jsonify({'success': False, 'error': 'Bot Token nicht konfiguriert'})
        
        monitor = TelegramChannelMonitor(bot_token)
        
        # Bot-Info abrufen
        async def get_bot_info():
            bot_info = await monitor.bot.get_me()
            return f"@{bot_info.username} ({bot_info.first_name})"
        
        bot_info = asyncio.run(get_bot_info())
        
        return jsonify({
            'success': True,
            'bot_info': bot_info,
            'message': 'Bot-Verbindung erfolgreich'
        })
        
    except Exception as e:
        logger.error(f"Bot-Test fehlgeschlagen: {e}")
        return jsonify({'success': False, 'error': str(e)})


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
