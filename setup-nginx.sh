#!/bin/bash

# Nginx-Setup für news.2b6.de
echo "Setting up Nginx configuration for news.2b6.de..."

# Backup der bestehenden Nginx-Konfiguration
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup.$(date +%Y%m%d_%H%M%S)

# Erstelle symbolischen Link zur news.2b6.de Konfiguration
sudo ln -sf $(pwd)/nginx/news.2b6.de.conf /etc/nginx/sites-available/news.2b6.de
sudo ln -sf /etc/nginx/sites-available/news.2b6.de /etc/nginx/sites-enabled/news.2b6.de

# Teste Nginx-Konfiguration
echo "Testing Nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration test successful!"
    echo "To reload Nginx, run: sudo systemctl reload nginx"
else
    echo "❌ Nginx configuration test failed!"
    echo "Please check the configuration and SSL certificate paths."
    exit 1
fi

echo ""
echo "📝 Next steps:"
echo "1. Update SSL certificate paths in nginx/news.2b6.de.conf"
echo "2. Make sure DNS points news.2b6.de to this server"
echo "3. Start the Docker containers: docker-compose up -d"
echo "4. Reload Nginx: sudo systemctl reload nginx"
echo "5. Visit https://news.2b6.de"
