"""
Route Registration and URL Patterns
"""

from flask import Blueprint, render_template

# Import all route blueprints
from .telegram import bp as telegram_bp
from .articles import bp as articles_bp


def register_routes(app):
    """Register all application routes"""
    
    # Telegram management routes
    app.register_blueprint(telegram_bp)
    
    # Article management routes  
    app.register_blueprint(articles_bp)
    
    # Main dashboard route (updated to include new features)
    from flask import render_template_string
    
    @app.route('/')
    def dashboard():
        """Main dashboard with mobile-first design"""
        from app.data import json_manager
        
        # Get statistics
        articles = json_manager.read('articles')
        sources = json_manager.read('sources')
        
        total_articles = len(articles.get('articles', {}))
        total_sources = len(sources.get('sources', {}))
        telegram_sources = sum(1 for s in sources.get('sources', {}).values() 
                              if s.get('type') == 'telegram')
        rated_articles = sum(1 for a in articles.get('articles', {}).values() 
                           if a.get('relevance_score'))
        
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
