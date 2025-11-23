# Deployment Configuration Files

This directory contains configuration files for deploying the Craigslist Lead Generation System to production.

## Directory Structure

```
deployment/
├── nginx/
│   └── craigslist-leads.conf    # Nginx reverse proxy configuration
├── systemd/
│   ├── craigslist-backend.service      # Backend API service
│   ├── craigslist-celery.service       # Celery worker service
│   └── craigslist-celery-beat.service  # Celery beat scheduler service
└── README.md                     # This file
```

## Installation Instructions

### 1. Install Systemd Services

```bash
# Copy service files to systemd directory
sudo cp deployment/systemd/*.service /etc/systemd/system/

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable services to start on boot
sudo systemctl enable craigslist-backend
sudo systemctl enable craigslist-celery
sudo systemctl enable craigslist-celery-beat

# Start services
sudo systemctl start craigslist-backend
sudo systemctl start craigslist-celery
sudo systemctl start craigslist-celery-beat

# Check service status
sudo systemctl status craigslist-backend
sudo systemctl status craigslist-celery
sudo systemctl status craigslist-celery-beat
```

### 2. Install Nginx Configuration

```bash
# Copy Nginx configuration
sudo cp deployment/nginx/craigslist-leads.conf /etc/nginx/sites-available/

# Update domain names and paths in the config
sudo nano /etc/nginx/sites-available/craigslist-leads.conf

# Test Nginx configuration
sudo nginx -t

# Enable site
sudo ln -s /etc/nginx/sites-available/craigslist-leads /etc/nginx/sites-enabled/

# Reload Nginx
sudo systemctl reload nginx
```

### 3. Setup SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run

# Certificate will auto-renew via cron
```

## Service Management

### View Logs

```bash
# Backend logs
sudo journalctl -u craigslist-backend -f

# Celery worker logs
sudo journalctl -u craigslist-celery -f

# Celery beat logs
sudo journalctl -u craigslist-celery-beat -f

# All services
sudo journalctl -u craigslist-* -f
```

### Restart Services

```bash
# Restart all services
sudo systemctl restart craigslist-backend craigslist-celery craigslist-celery-beat

# Restart individual service
sudo systemctl restart craigslist-backend
```

### Stop Services

```bash
# Stop all services
sudo systemctl stop craigslist-backend craigslist-celery craigslist-celery-beat

# Stop individual service
sudo systemctl stop craigslist-backend
```

## Configuration Notes

### Systemd Services

#### Backend Service
- **User:** `www-data` (change if needed)
- **Workers:** 4 (adjust based on CPU cores)
- **Port:** 8000 (internal, proxied by Nginx)
- **Restart Policy:** Always restart on failure
- **Logs:** journalctl + file logging

#### Celery Worker
- **Concurrency:** 4 workers (adjust based on workload)
- **Max Tasks Per Child:** 1000 (prevents memory leaks)
- **Time Limit:** 600 seconds per task
- **Logs:** `/var/www/craigslist-leads/logs/celery-worker.log`

#### Celery Beat
- **Purpose:** Scheduled task execution
- **Logs:** `/var/www/craigslist-leads/logs/celery-beat.log`

### Nginx Configuration

#### Features Configured
- ✓ HTTPS with TLS 1.2/1.3
- ✓ HTTP/2 support
- ✓ Reverse proxy to backend
- ✓ WebSocket support
- ✓ Rate limiting (60 requests/minute)
- ✓ Security headers (HSTS, CSP, etc.)
- ✓ Gzip compression
- ✓ Static file caching
- ✓ Let's Encrypt SSL

#### Rate Limiting
- **API endpoints:** 60 requests/minute (burst: 20)
- **Login endpoints:** 5 requests/minute
- Configure in `/etc/nginx/sites-available/craigslist-leads.conf`

## Security Checklist

Before going live, ensure:

- [ ] Updated domain names in Nginx config
- [ ] SSL certificates installed and valid
- [ ] Firewall configured (UFW/iptables)
- [ ] Service user (www-data) has minimal permissions
- [ ] Database credentials secured
- [ ] Redis access restricted
- [ ] API rate limiting enabled
- [ ] CORS properly configured (no wildcards)
- [ ] DEBUG=false in production environment
- [ ] Secret keys are unique and secure

## Monitoring

### Health Checks

```bash
# API health
curl https://api.yourdomain.com/health

# Service status
systemctl status craigslist-backend

# Check logs for errors
sudo journalctl -u craigslist-backend --since "1 hour ago" | grep ERROR
```

### Performance Monitoring

```bash
# CPU and memory usage
htop

# Disk usage
df -h

# Database connections
psql -U postgres -d craigslist_leads -c "SELECT count(*) FROM pg_stat_activity;"

# Redis memory
redis-cli info memory
```

## Troubleshooting

### Service won't start

```bash
# Check service logs
sudo journalctl -u craigslist-backend -n 100

# Verify environment file exists
ls -la /var/www/craigslist-leads/.env.production

# Check file permissions
sudo ls -la /var/www/craigslist-leads/backend/

# Test Python dependencies
cd /var/www/craigslist-leads/backend
source venv/bin/activate
python -c "import app.main"
```

### Nginx errors

```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log

# Verify upstream is running
curl http://localhost:8000/health
```

### High CPU/Memory usage

```bash
# Check process usage
ps aux | grep python

# Reduce Celery workers
# Edit: /etc/systemd/system/craigslist-celery.service
# Change: --concurrency=2
sudo systemctl daemon-reload
sudo systemctl restart craigslist-celery
```

## Updates and Maintenance

### Update Application

```bash
# Use deployment scripts
cd /var/www/craigslist-leads
./scripts/deploy_backend.sh production
./scripts/deploy_frontend.sh production

# Verify deployment
./scripts/health_check.sh production
```

### Update Nginx Configuration

```bash
# Edit config
sudo nano /etc/nginx/sites-available/craigslist-leads.conf

# Test changes
sudo nginx -t

# Apply changes
sudo systemctl reload nginx
```

### Update Systemd Services

```bash
# Edit service file
sudo nano /etc/systemd/system/craigslist-backend.service

# Reload daemon
sudo systemctl daemon-reload

# Restart service
sudo systemctl restart craigslist-backend
```

## Additional Resources

- [Full Deployment Guide](../DEPLOYMENT_GUIDE.md)
- [Quick Start Guide](../DEPLOYMENT_QUICK_START.md)
- [Backend Operations Guide](../backend/DEPLOYMENT_OPERATIONS_GUIDE.md)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Systemd Documentation](https://www.freedesktop.org/software/systemd/man/)

---

**Note:** Always backup your configuration files before making changes. Test changes in staging environment before applying to production.
