"""
JSON-basierter Datenmanager für Thread-sichere Datenhaltung
"""

import json
import os
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
from contextlib import contextmanager
import uuid
import shutil


class JSONManager:
    """Thread-sicherer JSON-Dateimanager"""
    
    def __init__(self, data_dir: str = "/app/data"):
        self.data_dir = data_dir
        self.locks = {}
        self._ensure_data_dir()
        
    def _ensure_data_dir(self):
        """Stelle sicher, dass das Datenverzeichnis existiert"""
        os.makedirs(self.data_dir, exist_ok=True)
        backup_dir = os.path.join(self.data_dir, "backups")
        os.makedirs(backup_dir, exist_ok=True)
    
    def _get_lock(self, filename: str) -> threading.RLock:
        """Hole oder erstelle einen Lock für eine spezifische Datei"""
        if filename not in self.locks:
            self.locks[filename] = threading.RLock()
        return self.locks[filename]
    
    def _get_filepath(self, filename: str) -> str:
        """Erstelle vollständigen Dateipfad"""
        return os.path.join(self.data_dir, f"{filename}.json")
    
    @contextmanager
    def _file_lock(self, filename: str):
        """Context Manager für File-Locking"""
        lock = self._get_lock(filename)
        lock.acquire()
        try:
            yield
        finally:
            lock.release()
    
    def read(self, filename: str) -> Dict[str, Any]:
        """Lese JSON-Datei Thread-sicher"""
        filepath = self._get_filepath(filename)
        
        with self._file_lock(filename):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except FileNotFoundError:
                return self._create_empty_structure(filename)
            except json.JSONDecodeError as e:
                print(f"JSON decode error in {filename}: {e}")
                return self._create_empty_structure(filename)
    
    def write(self, filename: str, data: Dict[str, Any], backup: bool = True):
        """Schreibe JSON-Datei Thread-sicher"""
        filepath = self._get_filepath(filename)
        
        with self._file_lock(filename):
            # Backup erstellen
            if backup and os.path.exists(filepath):
                self._create_backup(filename)
            
            # Metadata aktualisieren
            if 'metadata' in data:
                data['metadata']['last_updated'] = datetime.now().isoformat()
            
            # Atomisches Schreiben
            temp_filepath = f"{filepath}.tmp"
            try:
                with open(temp_filepath, 'w', encoding='utf-8') as f:
                    # Kompakte Speicherung für bessere Performance (Standard)
                    json.dump(data, f, separators=(',', ':'), ensure_ascii=False)
                
                # Atomic move
                os.replace(temp_filepath, filepath)
                
            except Exception as e:
                # Cleanup bei Fehler
                if os.path.exists(temp_filepath):
                    os.remove(temp_filepath)
                raise e
    
    def update(self, filename: str, updates: Dict[str, Any]):
        """Update spezifische Felder in JSON-Datei"""
        with self._file_lock(filename):
            data = self.read(filename)
            self._deep_update(data, updates)
            self.write(filename, data)
    
    def add_item(self, filename: str, item_data: Dict[str, Any], 
                 collection_key: str = None) -> str:
        """Füge neues Item zu Collection hinzu"""
        item_id = str(uuid.uuid4())
        item_data['id'] = item_id
        item_data['created_at'] = datetime.now().isoformat()
        
        with self._file_lock(filename):
            data = self.read(filename)
            
            # Bestimme Collection-Key
            if collection_key is None:
                collection_key = filename  # z.B. 'articles' für articles.json
            
            if collection_key not in data:
                data[collection_key] = {}
            
            data[collection_key][item_id] = item_data
            
            # Metadata aktualisieren
            if 'metadata' in data:
                data['metadata']['total_count'] = len(data[collection_key])
            
            self.write(filename, data)
            
        return item_id
    
    def get_item(self, filename: str, item_id: str, 
                 collection_key: str = None) -> Optional[Dict[str, Any]]:
        """Hole spezifisches Item"""
        data = self.read(filename)
        collection_key = collection_key or filename
        
        if collection_key in data and item_id in data[collection_key]:
            return data[collection_key][item_id]
        return None
    
    def delete_item(self, filename: str, item_id: str, 
                    collection_key: str = None):
        """Lösche Item aus Collection"""
        with self._file_lock(filename):
            data = self.read(filename)
            collection_key = collection_key or filename
            
            if collection_key in data and item_id in data[collection_key]:
                del data[collection_key][item_id]
                
                # Metadata aktualisieren
                if 'metadata' in data:
                    data['metadata']['total_count'] = len(data[collection_key])
                
                self.write(filename, data)
    
    def search(self, filename: str, filters: Dict[str, Any], 
               collection_key: str = None) -> List[Dict[str, Any]]:
        """Suche Items basierend auf Filtern"""
        data = self.read(filename)
        collection_key = collection_key or filename
        
        if collection_key not in data:
            return []
        
        results = []
        for item in data[collection_key].values():
            if self._matches_filters(item, filters):
                results.append(item)
        
        return results
    
    def _matches_filters(self, item: Dict[str, Any], 
                        filters: Dict[str, Any]) -> bool:
        """Prüfe ob Item den Filtern entspricht"""
        for key, value in filters.items():
            if '.' in key:
                # Nested key support: "metadata.relevance_score"
                if not self._get_nested_value(item, key.split('.')) == value:
                    return False
            else:
                if key not in item or item[key] != value:
                    return False
        return True
    
    def _get_nested_value(self, data: Dict, keys: List[str]) -> Any:
        """Hole Wert aus verschachtelter Struktur"""
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict):
        """Rekursives Dictionary-Update"""
        for key, value in update_dict.items():
            if (key in base_dict and isinstance(base_dict[key], dict) 
                and isinstance(value, dict)):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def _create_backup(self, filename: str):
        """Erstelle Backup der aktuellen Datei"""
        filepath = self._get_filepath(filename)
        if not os.path.exists(filepath):
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{filename}_{timestamp}.json"
        backup_filepath = os.path.join(self.data_dir, "backups", backup_filename)
        
        try:
            shutil.copy2(filepath, backup_filepath)
        except Exception as e:
            print(f"Backup creation failed for {filename}: {e}")
    
    def _create_empty_structure(self, filename: str) -> Dict[str, Any]:
        """Erstelle leere Grundstruktur für neue Dateien"""
        structures = {
            'sources': {
                "sources": {},
                "metadata": {
                    "version": "1.0",
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "total_count": 0
                },
                "indexes": {"by_type": {}, "by_status": {}}
            },
            'articles': {
                "articles": {},
                "metadata": {
                    "version": "1.0",
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "total_count": 0
                },
                "indexes": {
                    "by_date": {}, "by_source": {}, "by_relevance": {},
                    "by_sentiment": {}, "by_tags": {}
                }
            },
            'tags': {
                "tags": {},
                "metadata": {
                    "version": "1.0",
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "total_count": 0
                },
                "learning_data": {
                    "user_preferences": {},
                    "tag_weights": {},
                    "auto_suggestions": []
                }
            },
            'tweets': {
                "tweets": {},
                "metadata": {
                    "version": "1.0",
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "total_count": 0
                },
                "templates": {
                    "default": "🔥 {title}\n\n{summary}\n\n{url}",
                    "critical": "⚠️ {title}\n\n{summary}\n\n📖 {url}",
                    "analysis": "📊 {title}\n\n{analysis}\n\n{url}"
                }
            }
        }
        
        return structures.get(filename, {
            filename: {},
            "metadata": {
                "version": "1.0", 
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "total_count": 0
            }
        })
    
    def cleanup_old_backups(self, days: int = 7):
        """Lösche alte Backup-Dateien"""
        backup_dir = os.path.join(self.data_dir, "backups")
        if not os.path.exists(backup_dir):
            return
        
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        for filename in os.listdir(backup_dir):
            filepath = os.path.join(backup_dir, filename)
            if os.path.isfile(filepath):
                if os.path.getmtime(filepath) < cutoff_time:
                    try:
                        os.remove(filepath)
                    except Exception as e:
                        print(f"Could not delete old backup {filename}: {e}")


# Singleton-Instanz
json_manager = JSONManager()
