"""
Flask App Entry Point
"""

import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Für Docker-Container auf allen Interfaces lauschen
    host = '0.0.0.0'
    port = int(os.environ.get('PORT', 5020))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host=host, port=port, debug=debug)
