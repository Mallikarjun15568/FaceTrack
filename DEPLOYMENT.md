# FaceTrack Pro - Production Deployment Guide

## 🚀 Pre-Deployment Checklist

### 1. Environment Configuration
- [ ] Copy `.env.example` to `.env`
- [ ] Set strong `SECRET_KEY` (minimum 32 characters)
- [ ] Configure database credentials
- [ ] Set `APP_MODE=production`
- [ ] Set `DEBUG=False`
- [ ] Configure SMTP settings for email notifications

### 2. Database Setup
```bash
# Run database indexes for performance
mysql -u root -p facetrack_db < scripts/create_indexes.sql

# Verify indexes
mysql -u root -p facetrack_db -e "SHOW INDEX FROM attendance;"
```

### 3. Dependencies
```bash
# Install production dependencies
pip install -r requirements.txt

# Install production web server
pip install gunicorn
```

### 4. Security Hardening

#### Session Security
Ensure these are set in production `.env`:
```
APP_MODE=production
DEBUG=False
SESSION_COOKIE_SECURE=True  # Only over HTTPS
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
```

#### HTTPS Configuration
Use nginx or Apache as reverse proxy with SSL certificate:
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 5. Production Server

#### Using Gunicorn (Recommended)
```bash
# Production server with 4 workers
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 --access-logfile logs/access.log --error-logfile logs/error.log app:app
```

#### Systemd Service
Create `/etc/systemd/system/facetrack.service`:
```ini
[Unit]
Description=FaceTrack Pro Application
After=network.target mysql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/facetrack
Environment="PATH=/var/www/facetrack/venv/bin"
ExecStart=/var/www/facetrack/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 --timeout 120 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable facetrack
sudo systemctl start facetrack
sudo systemctl status facetrack
```

### 6. Logging Configuration
```bash
# Create log directory
mkdir -p logs
chmod 755 logs

# Rotate logs (create /etc/logrotate.d/facetrack)
/var/www/facetrack/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
}
```

### 7. Database Backup
```bash
# Create backup script
cat > /usr/local/bin/facetrack-backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/facetrack"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Database backup
mysqldump -u root -p facetrack_db | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete
EOF

chmod +x /usr/local/bin/facetrack-backup.sh

# Add to crontab (daily at 2 AM)
echo "0 2 * * * /usr/local/bin/facetrack-backup.sh" | crontab -
```

### 8. Performance Optimization

#### MySQL Configuration
Add to `/etc/mysql/my.cnf`:
```ini
[mysqld]
max_connections = 150
innodb_buffer_pool_size = 1G
query_cache_size = 64M
query_cache_type = 1
```

#### Application Monitoring
Install and configure:
- **New Relic** or **DataDog** for application monitoring
- **Prometheus + Grafana** for metrics
- **Sentry** for error tracking

### 9. Security Headers (Nginx)
```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self' https:;" always;
```

### 10. Testing Before Go-Live
```bash
# Test database connection
python -c "from db_utils import get_connection; conn = get_connection(); print('DB OK')"

# Test face recognition
python scripts/smoke_test.py

# Load test with Apache Bench
ab -n 1000 -c 10 https://your-domain.com/
```

## 📊 Production Monitoring

### Health Check Endpoint
Add to `app.py`:
```python
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'embeddings_loaded': len(face_encoder.embeddings),
        'database': 'connected'
    })
```

### Monitoring Metrics
- Database connection pool usage
- Face recognition response time
- API endpoint latency
- Error rates
- Memory usage
- CPU usage

## 🔐 Post-Deployment Security

1. **Change default admin password immediately**
2. **Enable firewall** (UFW/iptables)
3. **Set up fail2ban** for brute-force protection
4. **Regular security updates**
5. **SSL/TLS certificate renewal** (Let's Encrypt)

## 🆘 Troubleshooting

### Common Issues

**Database connection fails:**
```bash
# Check MySQL service
sudo systemctl status mysql

# Test connection
mysql -u root -p -e "SHOW DATABASES;"
```

**Face embeddings not loading:**
```bash
# Check logs
tail -f logs/app.log

# Reload embeddings
mysql -u root -p facetrack_db -e "SELECT COUNT(*) FROM face_data;"
```

**High memory usage:**
```bash
# Check process memory
ps aux | grep gunicorn

# Restart workers
sudo systemctl restart facetrack
```

## 📞 Support

For production support:
- Check logs: `logs/app.log`, `logs/error.log`
- Database logs: `/var/log/mysql/error.log`
- System logs: `journalctl -u facetrack -f`

---

**Last Updated:** January 2026
