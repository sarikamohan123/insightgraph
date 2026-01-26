# Deployment Guide

## Overview

This guide covers deploying InsightGraph to production environments following industry best practices.

---

## Quick Deploy (Free Tier) - Recommended

Deploy InsightGraph for **$0/month** using:
- **Frontend**: Vercel (instant, no cold starts)
- **Backend**: Render (750 free hours/month)
- **Database**: Neon (PostgreSQL with pgvector)
- **Redis**: Upstash (10K commands/day)
- **Monitoring**: UptimeRobot (keeps backend awake)

### Step 1: Create Free Accounts (5 minutes)

Sign up with GitHub at:
1. **Neon** - https://neon.tech (PostgreSQL)
2. **Upstash** - https://upstash.com (Redis)
3. **Render** - https://render.com (Backend)
4. **Vercel** - https://vercel.com (Frontend)
5. **UptimeRobot** - https://uptimerobot.com (Monitoring)

### Step 2: Set Up Neon Database (3 minutes)

1. Go to https://console.neon.tech
2. Click **"New Project"**
3. Name: `insightgraph`, Region: `US East`
4. Click **"Create Project"**
5. Copy the connection string (looks like):
   ```
   postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
6. **Enable pgvector**:
   - Go to **SQL Editor** in Neon dashboard
   - Run: `CREATE EXTENSION IF NOT EXISTS vector;`

### Step 3: Set Up Upstash Redis (2 minutes)

1. Go to https://console.upstash.com
2. Click **"Create Database"**
3. Name: `insightgraph`, Region: `US East 1`
4. Click **"Create"**
5. Copy the **REST URL** (looks like):
   ```
   rediss://default:xxx@xxx.upstash.io:6379
   ```

### Step 4: Deploy Backend to Render (5 minutes)

1. Go to https://dashboard.render.com
2. Click **"New" → "Web Service"**
3. Connect your GitHub repo: `sarikamohan123/insightgraph`
4. Configure:
   - **Name**: `insightgraph-api`
   - **Region**: `Oregon (US West)`
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
   - **Plan**: `Free`

5. Add Environment Variables (click "Advanced" → "Add Environment Variable"):
   ```
   GEMINI_API_KEY=your_gemini_api_key
   DATABASE_URL=postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require
   REDIS_URL=rediss://default:xxx@xxx.upstash.io:6379
   JWT_SECRET_KEY=<generate with: openssl rand -hex 32>
   FRONTEND_URL=https://insightgraph.vercel.app
   USE_LLM_EXTRACTOR=true
   ENVIRONMENT=production
   ```

6. Click **"Create Web Service"**
7. Wait for deployment (~3-5 minutes)
8. Note your backend URL: `https://insightgraph-api.onrender.com`

### Step 5: Run Database Migrations

After Render deploys, run migrations:

1. In Render dashboard, go to your service
2. Click **"Shell"** tab
3. Run:
   ```bash
   cd backend
   alembic upgrade head
   ```

### Step 6: Deploy Frontend to Vercel (3 minutes)

1. Go to https://vercel.com/new
2. Import your GitHub repo: `sarikamohan123/insightgraph`
3. Configure:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
4. Add Environment Variable:
   ```
   VITE_API_URL=https://insightgraph-api.onrender.com
   ```
5. Click **"Deploy"**
6. Wait for deployment (~1-2 minutes)
7. Note your frontend URL: `https://insightgraph.vercel.app`

### Step 7: Update Backend CORS

Go back to Render and update:
```
FRONTEND_URL=https://insightgraph.vercel.app
```
(Use your actual Vercel URL)

### Step 8: Set Up UptimeRobot (2 minutes)

1. Go to https://uptimerobot.com
2. Click **"Add New Monitor"**
3. Configure:
   - **Monitor Type**: `HTTP(s)`
   - **Friendly Name**: `InsightGraph API`
   - **URL**: `https://insightgraph-api.onrender.com/health`
   - **Monitoring Interval**: `5 minutes`
4. Click **"Create Monitor"**

This keeps your backend awake 24/7!

### Step 9: Test Your Deployment

1. Visit your frontend: `https://insightgraph.vercel.app`
2. Create an account
3. Create a test graph
4. Verify dark mode and mobile responsive work
5. Test export functionality

### Troubleshooting

**Backend shows 502/503 error**:
- Wait 30 seconds (cold start on first request)
- Check Render logs for errors
- Verify environment variables are set

**Database connection failed**:
- Verify DATABASE_URL has `?sslmode=require`
- Check Neon dashboard for connection issues

**CORS errors in browser**:
- Verify FRONTEND_URL matches your Vercel URL exactly
- Redeploy backend after changing FRONTEND_URL

**"Tables not found" error**:
- Run migrations: `alembic upgrade head` in Render Shell

---

## Traditional Deployment (Self-Hosted)

## Prerequisites

- Python 3.11+
- PostgreSQL 16+
- Redis 7+
- Git

## Architecture

```
┌─────────────────┐
│  Load Balancer  │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│ API 1 │ │ API 2 │  (Multiple instances)
└───┬───┘ └──┬────┘
    │        │
    └────┬───┘
         │
    ┌────┴─────────┐
    │              │
┌───▼────┐   ┌────▼────┐
│ Redis  │   │ Postgres│
└────────┘   └─────────┘
         │
    ┌────▼────┐
    │ Worker  │  (Background job processor)
    └─────────┘
```

## Deployment Steps

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Install Redis
sudo apt install redis-server -y
```

### 2. Database Setup

```bash
# Create database and user
sudo -u postgres psql

CREATE DATABASE insightgraph;
CREATE USER insightgraph_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE insightgraph TO insightgraph_user;
\q
```

### 3. Application Setup

```bash
# Clone repository
git clone https://github.com/sarikamohan123/insightgraph.git
cd insightgraph/backend

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Environment Configuration

Create `.env` file:

```bash
# Production environment variables
GEMINI_API_KEY=your_gemini_api_key
USE_LLM_EXTRACTOR=true
MAX_RETRIES=3
TIMEOUT_SECONDS=30

# CRITICAL: Set a secure API key
API_KEY=your_secure_random_api_key_here

# Database (use production credentials)
DATABASE_URL=postgresql://insightgraph_user:your_secure_password@localhost:5432/insightgraph

# Redis
REDIS_URL=redis://localhost:6379
```

**Generate secure API key:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 5. Database Migration (CRITICAL STEP)

**⚠️ IMPORTANT: Always run migrations BEFORE starting the application**

```bash
# Navigate to backend directory
cd backend

# Run migrations
alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Running upgrade  -> c2a0d09f419f, Add knowledge graph tables
```

**Verify tables exist:**
```bash
psql -U insightgraph_user -d insightgraph -c "\dt"
```

Should show:
```
          List of relations
 Schema |  Name  | Type  |      Owner
--------+--------+-------+-----------------
 public | edges  | table | insightgraph_user
 public | graphs | table | insightgraph_user
 public | nodes  | table | insightgraph_user
```

### 6. Start Application

#### Option A: Using Uvicorn (Development/Testing)

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

#### Option B: Using Gunicorn (Production)

```bash
cd backend
pip install gunicorn

# Single worker
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# With multiple workers (recommended)
gunicorn main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
```

### 7. Start Background Worker

The worker processes async jobs from the Redis queue.

```bash
cd backend
python worker.py
```

### 8. Verify Deployment

```bash
# Health check
curl http://localhost:8000/health

# Expected response
{"status":"ok","extractor":"LLM"}

# System stats
curl http://localhost:8000/stats

# Should show authentication enabled
{
  "authentication": {
    "enabled": true
  }
}
```

## Systemd Service (Production)

Create `/etc/systemd/system/insightgraph-api.service`:

```ini
[Unit]
Description=InsightGraph API
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/insightgraph/backend
Environment="PATH=/path/to/insightgraph/backend/.venv/bin"
ExecStart=/path/to/insightgraph/backend/.venv/bin/gunicorn main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/insightgraph-worker.service`:

```ini
[Unit]
Description=InsightGraph Background Worker
After=network.target redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/insightgraph/backend
Environment="PATH=/path/to/insightgraph/backend/.venv/bin"
ExecStart=/path/to/insightgraph/backend/.venv/bin/python worker.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable insightgraph-api
sudo systemctl enable insightgraph-worker
sudo systemctl start insightgraph-api
sudo systemctl start insightgraph-worker

# Check status
sudo systemctl status insightgraph-api
sudo systemctl status insightgraph-worker
```

## Nginx Reverse Proxy

Create `/etc/nginx/sites-available/insightgraph`:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/insightgraph /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## SSL/TLS with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d api.yourdomain.com
```

## Database Backup

### Automated Backup Script

Create `/usr/local/bin/backup-insightgraph.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/insightgraph"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U insightgraph_user insightgraph | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete
```

Add to crontab:
```bash
sudo crontab -e

# Daily backup at 2 AM
0 2 * * * /usr/local/bin/backup-insightgraph.sh
```

## Migration Workflow

### Creating New Migrations

```bash
cd backend

# After modifying models in models/database.py
alembic revision --autogenerate -m "Description of changes"

# Review the generated migration file
# Edit if needed: backend/alembic/versions/<hash>_description.py

# Test migration
alembic upgrade head

# If issues, rollback
alembic downgrade -1
```

### Deploying Migrations

```bash
# 1. Stop the application
sudo systemctl stop insightgraph-api

# 2. Backup database
pg_dump -U insightgraph_user insightgraph > backup_before_migration.sql

# 3. Pull latest code
git pull origin main

# 4. Run migrations
cd backend
alembic upgrade head

# 5. Restart application
sudo systemctl start insightgraph-api

# 6. Verify
curl http://localhost:8000/health
```

## Monitoring

### Health Checks

```bash
# Application health
curl http://localhost:8000/health

# System stats
curl http://localhost:8000/stats

# Database connectivity
psql -U insightgraph_user -d insightgraph -c "SELECT 1"

# Redis connectivity
redis-cli ping
```

### Log Files

```bash
# Application logs (systemd)
sudo journalctl -u insightgraph-api -f

# Worker logs
sudo journalctl -u insightgraph-worker -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Scaling

### Horizontal Scaling

1. Run multiple API instances behind load balancer
2. All instances connect to same PostgreSQL and Redis
3. Scale worker separately based on job queue depth

### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_graphs_created_at ON graphs(created_at DESC);
CREATE INDEX idx_nodes_graph_id ON nodes(graph_id);
CREATE INDEX idx_edges_graph_id ON edges(graph_id);
```

## Troubleshooting

### Issue: "Tables not found" on startup

**Cause:** Migrations not run

**Solution:**
```bash
cd backend
alembic upgrade head
```

### Issue: Database connection failed

**Cause:** Wrong credentials or DATABASE_URL

**Solution:**
1. Check `.env` file
2. Verify PostgreSQL is running: `sudo systemctl status postgresql`
3. Test connection: `psql -U insightgraph_user -d insightgraph`

### Issue: Redis connection failed

**Cause:** Redis not running

**Solution:**
```bash
sudo systemctl start redis
sudo systemctl enable redis
```

### Issue: 401 Unauthorized on all endpoints

**Cause:** API_KEY not set or wrong

**Solution:**
1. Check `.env` has `API_KEY` set
2. Restart application to load new config
3. Verify: `curl http://localhost:8000/stats` shows `"enabled": true`

## Security Checklist

- [ ] Set secure `API_KEY` (32+ bytes random)
- [ ] Use strong database password
- [ ] Enable SSL/TLS (HTTPS)
- [ ] Set up firewall (UFW)
- [ ] Restrict PostgreSQL to localhost
- [ ] Restrict Redis to localhost
- [ ] Regular backups configured
- [ ] Security updates enabled
- [ ] Rate limiting configured
- [ ] Log monitoring in place

## Performance Tuning

### PostgreSQL

Edit `/etc/postgresql/16/main/postgresql.conf`:
```
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB
maintenance_work_mem = 64MB
```

Restart: `sudo systemctl restart postgresql`

### Redis

Edit `/etc/redis/redis.conf`:
```
maxmemory 512mb
maxmemory-policy allkeys-lru
```

Restart: `sudo systemctl restart redis`

## Rollback Procedure

If deployment fails:

```bash
# 1. Stop application
sudo systemctl stop insightgraph-api

# 2. Rollback database
alembic downgrade -1

# 3. Rollback code
git checkout <previous-commit>

# 4. Restart
sudo systemctl start insightgraph-api
```

## Support

For issues, check:
- Application logs: `journalctl -u insightgraph-api`
- Database logs: `/var/log/postgresql/postgresql-16-main.log`
- Redis logs: `/var/log/redis/redis-server.log`
