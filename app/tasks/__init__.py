"""
Tasks package initialization
"""

from .scraping_tasks import celery_app, monitor_telegram_task, cleanup_old_articles_task

__all__ = ['celery_app', 'monitor_telegram_task', 'cleanup_old_articles_task']
