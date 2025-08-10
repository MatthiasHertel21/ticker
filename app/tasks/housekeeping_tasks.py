"""
Housekeeping Tasks für automatische Datenbereinigung
Entfernt alte Artikel, Medien und Backups basierend auf Konfiguration
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path

from app.celery_app import celery_app
from app.data.json_manager import JSONManager
from config.config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HousekeepingManager:
    """Verwaltet die automatische Bereinigung alter Daten"""
    
    def __init__(self):
        self.json_manager = JSONManager()
        self.data_dir = Path(Config.DATA_DIR)
        self.media_dir = self.data_dir / 'media'
        self.backup_dir = self.data_dir / 'backups'
        
    def cleanup_old_articles(self, days: int = None) -> Dict[str, Any]:
        """
        Entfernt Artikel älter als X Tage
        
        Args:
            days: Anzahl Tage (Standard: Config.CLEANUP_DAYS)
            
        Returns:
            Dict mit Cleanup-Statistiken
        """
        days = days or Config.CLEANUP_DAYS
        cutoff_date = datetime.now() - timedelta(days=days)
        
        logger.info(f"🧹 Starte Article-Cleanup: Lösche Artikel älter als {days} Tage ({cutoff_date.date()})")
        
        # Lade aktuelle Artikel
        articles_data = self.json_manager.read('articles')
        original_count = len(articles_data.get('articles', []))
        
        # Filtere alte Artikel
        cleaned_articles = []
        removed_articles = []
        removed_media_files = []
        
        for article in articles_data.get('articles', []):
            # Parse scraped_date
            try:
                scraped_date = datetime.fromisoformat(
                    article.get('scraped_date', '').replace('Z', '+00:00').replace('+00:00', '')
                )
                
                if scraped_date >= cutoff_date:
                    cleaned_articles.append(article)
                else:
                    removed_articles.append(article)
                    # Sammle zugehörige Media-Files
                    if 'media_files' in article:
                        removed_media_files.extend(article['media_files'])
                        
            except (ValueError, AttributeError) as e:
                logger.warning(f"⚠️ Fehler beim Parsen des Datums für Artikel {article.get('id', 'unknown')}: {e}")
                # Bei Parsing-Fehlern: Artikel behalten
                cleaned_articles.append(article)
        
        # Speichere bereinigte Artikel
        articles_data['articles'] = cleaned_articles
        self.json_manager.save_data('articles', articles_data)
        
        # Entferne zugehörige Media-Files
        removed_media_count = self._cleanup_media_files(removed_media_files)
        
        stats = {
            'original_count': original_count,
            'removed_count': len(removed_articles),
            'remaining_count': len(cleaned_articles),
            'removed_media_files': removed_media_count,
            'cutoff_date': cutoff_date.isoformat(),
            'cleanup_date': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Article-Cleanup abgeschlossen: {stats['removed_count']} Artikel entfernt, {stats['remaining_count']} behalten")
        return stats
    
    def cleanup_orphaned_media(self) -> Dict[str, Any]:
        """
        Entfernt Media-Files ohne zugehörige Artikel
        
        Returns:
            Dict mit Cleanup-Statistiken
        """
        logger.info("🧹 Starte Orphaned-Media-Cleanup")
        
        if not self.media_dir.exists():
            return {'removed_count': 0, 'message': 'Media-Verzeichnis existiert nicht'}
        
        # Sammle alle verwendeten Media-Files aus Artikeln
        articles_data = self.json_manager.read('articles')
        used_media_files = set()
        
        for article in articles_data.get('articles', []):
            # Media-Files aus verschiedenen Feldern sammeln
            if 'media_files' in article:
                used_media_files.update(article['media_files'])
            
            # Prüfe Content auf Telegram-Photos
            content = article.get('content', '')
            if 'telegram_photo_' in content:
                # Extrahiere Dateinamen aus Content
                import re
                photo_matches = re.findall(r'telegram_photo_\d+\.jpg', content)
                used_media_files.update(photo_matches)
        
        # Finde alle Media-Files im Verzeichnis
        all_media_files = set()
        for file_path in self.media_dir.glob('*'):
            if file_path.is_file():
                all_media_files.add(file_path.name)
        
        # Identifiziere verwaiste Files
        orphaned_files = all_media_files - used_media_files
        removed_count = 0
        
        for filename in orphaned_files:
            file_path = self.media_dir / filename
            try:
                file_path.unlink()
                removed_count += 1
                logger.info(f"🗑️ Entfernt: {filename}")
            except Exception as e:
                logger.error(f"❌ Fehler beim Entfernen von {filename}: {e}")
        
        stats = {
            'total_media_files': len(all_media_files),
            'used_media_files': len(used_media_files),
            'orphaned_files': len(orphaned_files),
            'removed_count': removed_count,
            'cleanup_date': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Orphaned-Media-Cleanup abgeschlossen: {removed_count} verwaiste Dateien entfernt")
        return stats
    
    def cleanup_old_backups(self, days: int = None) -> Dict[str, Any]:
        """
        Entfernt Backup-Files älter als X Tage
        
        Args:
            days: Anzahl Tage (Standard: Config.BACKUP_RETENTION_DAYS)
            
        Returns:
            Dict mit Cleanup-Statistiken
        """
        days = days or Config.BACKUP_RETENTION_DAYS
        cutoff_date = datetime.now() - timedelta(days=days)
        
        logger.info(f"🧹 Starte Backup-Cleanup: Lösche Backups älter als {days} Tage ({cutoff_date.date()})")
        
        if not self.backup_dir.exists():
            return {'removed_count': 0, 'message': 'Backup-Verzeichnis existiert nicht'}
        
        removed_count = 0
        total_size_freed = 0
        
        for file_path in self.backup_dir.glob('*.json'):
            try:
                # Parse Datum aus Dateiname (Format: articles_YYYYMMDD_HHMMSS.json)
                filename = file_path.name
                if '_' in filename:
                    parts = filename.split('_')
                    if len(parts) >= 3:
                        date_str = parts[1]  # YYYYMMDD
                        time_str = parts[2].replace('.json', '')  # HHMMSS
                        
                        backup_date = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                        
                        if backup_date < cutoff_date:
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            removed_count += 1
                            total_size_freed += file_size
                            logger.info(f"🗑️ Entfernt: {filename}")
                            
            except (ValueError, IndexError) as e:
                logger.warning(f"⚠️ Fehler beim Parsen des Backup-Datums für {filename}: {e}")
            except Exception as e:
                logger.error(f"❌ Fehler beim Entfernen von {filename}: {e}")
        
        stats = {
            'removed_count': removed_count,
            'size_freed_bytes': total_size_freed,
            'size_freed_mb': round(total_size_freed / 1024 / 1024, 2),
            'cutoff_date': cutoff_date.isoformat(),
            'cleanup_date': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Backup-Cleanup abgeschlossen: {removed_count} Backups entfernt, {stats['size_freed_mb']} MB freigegeben")
        return stats
    
    def _cleanup_media_files(self, media_files: List[str]) -> int:
        """
        Hilfsmethode: Entfernt spezifische Media-Files
        
        Args:
            media_files: Liste der zu entfernenden Dateinamen
            
        Returns:
            Anzahl erfolgreich entfernter Files
        """
        if not self.media_dir.exists():
            return 0
        
        removed_count = 0
        for filename in media_files:
            file_path = self.media_dir / filename
            if file_path.exists() and file_path.is_file():
                try:
                    file_path.unlink()
                    removed_count += 1
                    logger.info(f"🗑️ Media entfernt: {filename}")
                except Exception as e:
                    logger.error(f"❌ Fehler beim Entfernen von {filename}: {e}")
        
        return removed_count
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Liefert aktuelle Speicher-Statistiken
        
        Returns:
            Dict mit Speicher-Informationen
        """
        def get_dir_size(path: Path) -> int:
            """Berechnet Verzeichnisgröße rekursiv"""
            if not path.exists():
                return 0
            
            total_size = 0
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    try:
                        total_size += file_path.stat().st_size
                    except (OSError, IOError):
                        pass
            return total_size
        
        def count_files(path: Path, pattern: str = '*') -> int:
            """Zählt Files in Verzeichnis"""
            if not path.exists():
                return 0
            return len(list(path.glob(pattern)))
        
        # Artikel-Statistiken
        articles_data = self.json_manager.read('articles')
        article_count = len(articles_data.get('articles', []))
        
        # Größen berechnen
        data_size = get_dir_size(self.data_dir)
        media_size = get_dir_size(self.media_dir)
        backup_size = get_dir_size(self.backup_dir)
        
        # File-Counts
        media_count = count_files(self.media_dir, '*.jpg') + count_files(self.media_dir, '*.png')
        backup_count = count_files(self.backup_dir, '*.json')
        
        stats = {
            'articles': {
                'count': article_count,
                'size_mb': round(get_dir_size(self.data_dir / 'articles.json') / 1024 / 1024, 2)
            },
            'media': {
                'count': media_count,
                'size_mb': round(media_size / 1024 / 1024, 2)
            },
            'backups': {
                'count': backup_count,
                'size_mb': round(backup_size / 1024 / 1024, 2)
            },
            'total': {
                'size_mb': round(data_size / 1024 / 1024, 2),
                'size_gb': round(data_size / 1024 / 1024 / 1024, 2)
            },
            'generated_at': datetime.now().isoformat()
        }
        
        return stats
    
    def full_cleanup(self) -> Dict[str, Any]:
        """
        Führt komplette Bereinigung durch
        
        Returns:
            Dict mit allen Cleanup-Statistiken
        """
        logger.info("🧹 Starte vollständige Datenbereinigung")
        
        results = {
            'start_time': datetime.now().isoformat(),
            'storage_before': self.get_storage_stats(),
        }
        
        # 1. Alte Artikel bereinigen
        results['articles_cleanup'] = self.cleanup_old_articles()
        
        # 2. Verwaiste Media-Files bereinigen
        results['orphaned_media_cleanup'] = self.cleanup_orphaned_media()
        
        # 3. Alte Backups bereinigen
        results['backup_cleanup'] = self.cleanup_old_backups()
        
        # 4. Nach-Statistiken
        results['storage_after'] = self.get_storage_stats()
        results['end_time'] = datetime.now().isoformat()
        
        # Berechne eingesparten Speicher
        before_mb = results['storage_before']['total']['size_mb']
        after_mb = results['storage_after']['total']['size_mb']
        results['storage_saved_mb'] = round(before_mb - after_mb, 2)
        
        logger.info(f"✅ Vollständige Bereinigung abgeschlossen: {results['storage_saved_mb']} MB freigegeben")
        return results


# Celery Tasks
@celery_app.task(name='housekeeping.cleanup_old_articles')
def cleanup_old_articles_task(days: int = None):
    """Celery Task: Alte Artikel bereinigen"""
    manager = HousekeepingManager()
    return manager.cleanup_old_articles(days)


@celery_app.task(name='housekeeping.cleanup_orphaned_media')
def cleanup_orphaned_media_task():
    """Celery Task: Verwaiste Media-Files bereinigen"""
    manager = HousekeepingManager()
    return manager.cleanup_orphaned_media()


@celery_app.task(name='housekeeping.cleanup_old_backups')
def cleanup_old_backups_task(days: int = None):
    """Celery Task: Alte Backups bereinigen"""
    manager = HousekeepingManager()
    return manager.cleanup_old_backups(days)


@celery_app.task(name='housekeeping.full_cleanup')
def full_cleanup_task():
    """Celery Task: Vollständige Bereinigung"""
    manager = HousekeepingManager()
    return manager.full_cleanup()


@celery_app.task(name='housekeeping.get_storage_stats')
def get_storage_stats_task():
    """Celery Task: Speicher-Statistiken abrufen"""
    manager = HousekeepingManager()
    return manager.get_storage_stats()
