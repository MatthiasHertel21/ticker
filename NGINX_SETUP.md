# Nginx Setup für news.2b6.de

## 1. Nginx-Konfiguration installieren

```bash
# Konfiguration kopieren
sudo cp /home/ga/ticker/nginx/news.2b6.de.conf /etc/nginx/sites-available/

# Site aktivieren
sudo ln -s /etc/nginx/sites-available/news.2b6.de.conf /etc/nginx/sites-enabled/
```

## 2. SSL-Zertifikat konfigurieren

Bearbeite die Datei `/etc/nginx/sites-available/news.2b6.de.conf` und passe die SSL-Pfade an:

```nginx
# SSL-Zertifikat (anpassen an dein Setup)
ssl_certificate /path/to/your/news.2b6.de.crt;
ssl_certificate_key /path/to/your/news.2b6.de.key;
```

## 3. DNS-Eintrag prüfen

Stelle sicher, dass `news.2b6.de` auf deinen Server zeigt:

```bash
# DNS-Auflösung testen
nslookup news.2b6.de
```

## 4. Nginx testen und neu laden

```bash
# Konfiguration testen
sudo nginx -t

# Bei erfolgreichem Test: Nginx neu laden
sudo systemctl reload nginx
```

## 5. Firewall anpassen (falls nötig)

```bash
# Port 80 und 443 öffnen
sudo ufw allow 80
sudo ufw allow 443
```

## 6. Testen

Nach dem Setup solltest du die App erreichen können über:
- http://news.2b6.de (→ Weiterleitung zu HTTPS)
- https://news.2b6.de

## Aktueller Status

✅ **Docker-Setup**: Erfolgreich
- Flask-App läuft auf Port 5020
- Redis läuft auf Port 6379
- Health-Check funktioniert: http://localhost:5020/health

✅ **JSON-Datenhaltung**: Implementiert
- Thread-sicherer JSON-Manager
- Automatische Backups
- CRUD-Operationen

🔄 **Nächste Schritte**:
1. Nginx-Setup abschließen
2. Telegram-Integration starten
3. Mobile-First UI implementieren

## Troubleshooting

Falls Probleme auftreten:

```bash
# Container-Status prüfen
sudo docker-compose ps

# Logs anzeigen
sudo docker-compose logs webapp

# Nginx-Logs prüfen
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```
