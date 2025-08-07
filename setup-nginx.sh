#!/bin/bash

# Nginx Setup Script für news.2b6.de
# Führe dieses Script mit sudo aus: sudo bash setup-nginx.sh

echo "🚀 Setting up Nginx for news.2b6.de..."

# Prüfe ob Nginx installiert ist
if ! command -v nginx &> /dev/null; then
    echo "❌ Nginx ist nicht installiert. Installiere zuerst Nginx:"
    echo "   sudo apt update && sudo apt install nginx"
    exit 1
fi

# Backup der aktuellen Nginx-Konfiguration
if [ -f "/etc/nginx/sites-available/news.2b6.de.conf" ]; then
    echo "📦 Erstelle Backup der existierenden Konfiguration..."
    cp /etc/nginx/sites-available/news.2b6.de.conf /etc/nginx/sites-available/news.2b6.de.conf.backup.$(date +%Y%m%d_%H%M%S)
fi

# Kopiere Nginx-Konfiguration
echo "📋 Kopiere Nginx-Konfiguration..."
cp nginx/news.2b6.de.conf /etc/nginx/sites-available/

# Aktiviere die Site
echo "🔗 Aktiviere news.2b6.de Site..."
ln -sf /etc/nginx/sites-available/news.2b6.de.conf /etc/nginx/sites-enabled/

# Teste Nginx-Konfiguration
echo "🧪 Teste Nginx-Konfiguration..."
if nginx -t; then
    echo "✅ Nginx-Konfiguration ist gültig"
    
    # Reload Nginx
    echo "🔄 Lade Nginx neu..."
    systemctl reload nginx
    
    echo ""
    echo "🎉 Nginx-Setup erfolgreich abgeschlossen!"
    echo ""
    echo "📝 Nächste Schritte:"
    echo "1. SSL-Zertifikat-Pfade in /etc/nginx/sites-available/news.2b6.de.conf anpassen"
    echo "   - ssl_certificate /path/to/your/news.2b6.de.crt;"
    echo "   - ssl_certificate_key /path/to/your/news.2b6.de.key;"
    echo ""
    echo "2. DNS-Eintrag prüfen:"
    echo "   nslookup news.2b6.de"
    echo ""
    echo "3. Firewall-Ports öffnen (falls nötig):"
    echo "   sudo ufw allow 80"
    echo "   sudo ufw allow 443"
    echo ""
    echo "4. Nach SSL-Setup testen:"
    echo "   curl https://news.2b6.de/health"
    echo ""
    echo "🔗 App ist erreichbar unter:"
    echo "   - http://localhost:5020 (direkter Docker-Zugriff)"
    echo "   - https://news.2b6.de (nach SSL-Setup)"
    
else
    echo "❌ Nginx-Konfiguration hat Fehler. Bitte prüfe die Konfiguration."
    exit 1
fi
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
