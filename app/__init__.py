"""
Flask App Factory
"""

from flask import Flask
from config.config import get_config


def create_app():
    app = Flask(__name__)
    config = get_config()
    app.config.from_object(config)
    
    # Basis-Route für Health Check
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'news-aggregator'}, 200
    
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
