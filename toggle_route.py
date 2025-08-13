"""
Standalone Sources Toggle Route
"""

from flask import Blueprint, request, jsonify
import json
import os
import logging
from datetime import datetime

# Blueprint erstellen
toggle_bp = Blueprint('sources_toggle', __name__, url_prefix='/sources')

logger = logging.getLogger(__name__)

@toggle_bp.route('/toggle-status', methods=['POST'])
def toggle_source_status():
    """Status einer Quelle umschalten (aktiv/inaktiv)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Keine JSON-Daten empfangen'}), 400
            
        source_identifier = data.get('source_name')
        new_status = data.get('enabled')
        
        if not source_identifier:
            return jsonify({'error': 'Quellenidentifier erforderlich'}), 400
        
        if new_status is None:
            return jsonify({'error': 'Status erforderlich'}), 400
        
        logger.info(f"Toggle request for source: {source_identifier}, status: {new_status}")
        
        # Direkter Zugriff auf JSON-Datei
        sources_file = '/home/ga/ticker/data/sources.json'
        
        if not os.path.exists(sources_file):
            return jsonify({'error': 'Sources-Datei nicht gefunden'}), 404
        
        # JSON-Datei lesen
        with open(sources_file, 'r', encoding='utf-8') as f:
            sources_data = json.load(f)
        
        # Prüfen ob neue Struktur (mit sources Array) oder alte Struktur
        if isinstance(sources_data, dict) and 'sources' in sources_data:
            sources = sources_data['sources']
        else:
            sources = sources_data if isinstance(sources_data, list) else []
        
        # Quelle finden und Status ändern
        source_found = False
        source_name = source_identifier
        
        for source in sources:
            # Prüfen auf verschiedene Identifier (ID, Name, source_name)
            if (source.get('id') == source_identifier or 
                source.get('name') == source_identifier or 
                source.get('source_name') == source_identifier):
                
                source['enabled'] = bool(new_status)
                source['updated_at'] = datetime.now().isoformat()
                source_found = True
                source_name = source.get('name', source.get('source_name', source_identifier))
                logger.info(f"Found and updated source: {source_name}")
                break
        
        if not source_found:
            logger.warning(f"Source not found: {source_identifier}")
            return jsonify({'error': f'Quelle "{source_identifier}" nicht gefunden'}), 404
        
        # Änderungen speichern
        with open(sources_file, 'w', encoding='utf-8') as f:
            json.dump(sources_data, f, indent=2, ensure_ascii=False)
        
        # Erfolgsmeldung
        status_text = "aktiviert" if new_status else "deaktiviert"
        message = f"Quelle '{source_name}' wurde {status_text}"
        
        logger.info(f"Source status geändert: {source_identifier} -> {status_text}")
        
        return jsonify({
            'success': True,
            'message': message,
            'source_name': source_name,
            'enabled': bool(new_status)
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Umschalten des Quellenstatus: {e}", exc_info=True)
        return jsonify({'error': f'Fehler beim Ändern des Status: {str(e)}'}), 500
