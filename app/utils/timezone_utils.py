"""
Zeitzone-Hilfsfunktionen für einheitliche Zeitverwaltung
"""

from datetime import datetime
import pytz


def get_cet_time():
    """
    Aktuelle Zeit in CET/CEST Zeitzone (Europa/Berlin)
    Automatische Umstellung zwischen Sommer- und Winterzeit
    """
    cet = pytz.timezone('Europe/Berlin')
    return datetime.now(cet)


def get_utc_time():
    """Aktuelle Zeit in UTC"""
    return datetime.now(pytz.UTC)


def convert_to_cet(dt):
    """
    Konvertiert ein datetime-Objekt nach CET
    
    Args:
        dt: datetime object (mit oder ohne Zeitzone)
    
    Returns:
        datetime object in CET/CEST
    """
    cet = pytz.timezone('Europe/Berlin')
    
    # Wenn kein Timezone-Info vorhanden, als UTC interpretieren
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    
    return dt.astimezone(cet)


def get_cet_timestamp():
    """Aktueller CET-Zeitstempel im ISO-Format"""
    return get_cet_time().isoformat()


def parse_iso_to_cet(iso_string):
    """
    Parst ISO-Zeitstring und konvertiert nach CET
    
    Args:
        iso_string: ISO datetime string
    
    Returns:
        datetime object in CET
    """
    # Parse ISO string
    if iso_string.endswith('Z'):
        iso_string = iso_string.replace('Z', '+00:00')
    
    dt = datetime.fromisoformat(iso_string)
    return convert_to_cet(dt)
