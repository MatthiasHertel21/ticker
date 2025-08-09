"""
Flask App Factory
"""

from flask import Flask
from config.config import get_config


def create_app():
    app = Flask(__name__)
    config = get_config()
    app.config.from_object(config)
    
    # Enable auto-reload for development
    import os
    if app.config.get('ENV') == 'development' or os.getenv('FLASK_ENV') == 'development':
        app.config['DEBUG'] = True
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.jinja_env.auto_reload = True
    
    # Register template filters
    from app.utils.template_filters import register_template_filters
    register_template_filters(app)
    
    # Global context processor for article count
    @app.context_processor
    def inject_article_count():
        from app.data import json_manager
        try:
            articles = json_manager.read('articles')
            articles_data = articles.get('articles', [])
            if isinstance(articles_data, list):
                article_count = len(articles_data)
            else:
                article_count = len(list(articles_data.values()))
            return dict(global_article_count=article_count)
        except:
            return dict(global_article_count=0)
    
    # Register all application routes
    from app.routes import register_routes
    register_routes(app)
    
    return app
    
    # Basis-Route
    @app.route('/')
    def index():
        return '''
        <h1>News Aggregator</h1>
        <p>Mobile-First News Aggregator mit KI-Integration</p>
        <p>Status: Entwicklung Phase 1</p>
        <a href="/health">Health Check</a>
        '''
    
    return app
