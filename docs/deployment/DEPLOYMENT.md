# 🚀 Deployment Guide

## Quick Start (Local Docker)

```bash
# 1. Clone
git clone <repo>
cd crime-intelligence-platform

# 2. Configure
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# Edit both files with your secrets

# 3. Place ML artifacts
cp -r /path/to/ml-outputs/* backend/app/ml_artifacts/

# 4. Build & run
docker-compose -f deployment/docker/docker-compose.yml up -d

# Frontend: http://localhost
# Backend:  http://localhost:8000
# API docs: http://localhost:8000/docs
```

---

## Production Deployment

### 1. Supabase Setup

1. Create a project at [supabase.com](https://supabase.com)
2. Go to SQL Editor and run migrations in order:
   ```
   database/migrations/0001_initial_schema.sql
   database/policies/rls_policies.sql
   database/functions/helper_functions.sql
   database/seeds/001_default_admin.sql
   ```
3. Get credentials from **Project Settings → API**:
   - Project URL
   - Anon public key
   - Service role key
   - JWT secret
4. Create your admin user in **Authentication → Users**

### 2. Backend (Railway)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Init
cd backend
railway init

# Set environment variables
railway variables set APP_ENV=production
railway variables set SUPABASE_URL=...
railway variables set SUPABASE_JWT_SECRET=...
# ... (see backend/.env.example for all vars)

# Upload ML artifacts
railway run bash
mkdir -p /app/ml_artifacts
# (upload via scp or volume mount)

# Deploy
railway up
```

**Health check**: `https://<your-app>.up.railway.app/health`

### 3. Frontend (Vercel)

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
cd frontend
vercel --prod

# Set environment variables in Vercel dashboard:
# VITE_API_BASE_URL = https://<railway-app>.up.railway.app/api/v1
# VITE_SUPABASE_URL = ...
# VITE_SUPABASE_ANON_KEY = ...
# VITE_MAPBOX_PUBLIC_TOKEN = ...
```

### 4. CI/CD (GitHub Actions)

Set the following secrets in your GitHub repo:
- `VERCEL_TOKEN`
- `RAILWAY_TOKEN`
- `VITE_API_BASE_URL`
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_MAPBOX_PUBLIC_TOKEN`
- `SUPABASE_URL`, `SUPABASE_JWT_SECRET`, etc. (for backend CI)

Push to `main` to trigger:
1. CI (lint + test)
2. Deploy backend to Railway
3. Deploy frontend to Vercel

---

## Environment Variables Reference

| Variable | Required | Default |
|---|---|---|
| `SUPABASE_URL` | ✅ | — |
| `SUPABASE_ANON_KEY` | ✅ | — |
| `SUPABASE_SERVICE_ROLE_KEY` | ✅ | — |
| `SUPABASE_JWT_SECRET` | ✅ | — |
| `DATABASE_URL` | ✅ | — |
| `REDIS_URL` | ✅ | — |
| `MAPBOX_PUBLIC_TOKEN` | ✅ | — |
| `APP_ENV` | — | `development` |
| `CORS_ORIGINS` | — | `http://localhost:5173` |

---

## Monitoring

- **Sentry**: Set `SENTRY_DSN` for error tracking
- **Prometheus**: Set `PROMETHEUS_ENABLED=true` and scrape `/metrics`
- **Logs**: JSON format with `LOG_FORMAT=json` for aggregation

## Scaling

- Backend is stateless — scale horizontally with `WORKERS` env var
- Redis is shared across backend instances
- Supabase scales automatically
- Vercel CDN handles frontend traffic
