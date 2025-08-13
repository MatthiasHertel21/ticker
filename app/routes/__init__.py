"""
Route Registration and URL Patterns
"""

from flask import Blueprint, render_template

"""
Routes Package
"""

from flask import Flask
from .main import bp as main_bp
from .articles import bp as articles_bp
# from .telegram import bp as telegram_bp  # Temporär deaktiviert
# from .tasks import bp as tasks_bp  # Temporär deaktiviert
# from .tweets import bp as tweets_bp  # Temporär deaktiviert - benötigt OpenAI
from .housekeeping import housekeeping_bp
from .monitoring import bp as monitoring_bp
from .status import bp as status_bp
from .sources import sources_bp  # Multi-Source-Management


def register_routes(app: Flask):
    """Register all route blueprints"""
    app.register_blueprint(main_bp)
    app.register_blueprint(articles_bp)
    # app.register_blueprint(telegram_bp)  # Temporär deaktiviert
    # app.register_blueprint(tasks_bp)  # Temporär deaktiviert
    # app.register_blueprint(tweets_bp)  # Temporär deaktiviert - benötigt OpenAI
    app.register_blueprint(housekeeping_bp)
    app.register_blueprint(monitoring_bp)
    app.register_blueprint(status_bp)
    app.register_blueprint(sources_bp)  # Multi-Source-Management    # Main dashboard route (updated to include new features)
    from flask import render_template_string
    
    @app.route('/')
    def dashboard():
        """Main dashboard with mobile-first design"""
        from app.data import json_manager
        
        # Get statistics
        articles = json_manager.read('articles')
        sources = json_manager.read('sources')
        
        # Handle both list and dict structure for articles
        articles_data = articles.get('articles', [])
        if isinstance(articles_data, list):
            total_articles = len(articles_data)
            rated_articles = sum(1 for a in articles_data if a.get('relevance_score'))
        else:
            total_articles = len(articles_data)
            rated_articles = sum(1 for a in articles_data.values() if a.get('relevance_score'))
        
        total_sources = len(sources.get('sources', {}))
        telegram_sources = sum(1 for s in sources.get('sources', {}).values() 
                              if s.get('type') == 'telegram')
        
        # Check if Telegram is configured
        import os
        telegram_configured = bool(os.getenv('TELEGRAM_BOT_TOKEN'))
        
        return render_template('dashboard.html',
                             total_articles=total_articles,
                             total_sources=total_sources,
                             telegram_sources=telegram_sources,
                             rated_articles=rated_articles,
                             telegram_configured=telegram_configured,
                             show_sidebar=False)
    
    # Health check route
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        from app.data import json_manager
        import os
        from datetime import datetime
        
        try:
            # Test JSON manager
            json_manager.read('sources')
            
            # Check critical environment variables
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            
            return {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'telegram_configured': bool(bot_token),
                'data_directory': os.path.exists('/app/data')
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}, 500
