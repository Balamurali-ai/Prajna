# Prajna — Geospatial Crime Pattern Intelligence Platform

> A full-stack police command-center dashboard for crime intelligence, risk rankings, geospatial hotspot visualization, and ML explainability.

[![License](https://img.shields.io/badge/license-MIT-green)](#license)
[![Frontend](https://img.shields.io/badge/Frontend-React%2019-61dafb)](#)
[![Backend](https://img.shields.io/badge/Backend-FastAPI-009688)](#)
[![Database](https://img.shields.io/badge/Database-Supabase-3ecf8e)](#)
[![ET AI Hackathon 2026](https://img.shields.io/badge/Hackathon-ET%20AI%202026-blue)](#)

---

## Overview

Prajna ingests pre-computed outputs from an ML pipeline and presents actionable crime intelligence to police command staff via a real-time dashboard. The platform covers:

- District-level **risk scoring** and priority rankings
- H3 hexagon-based **crime hotspot** detection and GeoJSON mapping
- **SHAP-based explainability** for model transparency
- **Analytics** — trends, seasonality, crime categories, neighbor influence
- **Report generation** (PDF, CSV, JSON, GeoJSON) with async download
- **Real-time** dashboard updates via WebSocket
- **Role-based access control** (Admin, Officer, Analyst)

The ML pipeline (`ml/`) trains the models and exports artifacts. The backend (`backend/`) reads those artifacts and serves them via REST/WebSocket APIs. The frontend (`frontend/`) renders the dashboard.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 19, TypeScript, Vite, TailwindCSS, Radix UI, TanStack Query, Zustand, Recharts, Mapbox GL JS |
| **Backend** | FastAPI, SQLAlchemy 2.0 (async), Pydantic v2, Redis, Uvicorn |
| **Database** | Supabase PostgreSQL with Row Level Security |
| **Auth** | Supabase Auth (JWT, RBAC) |
| **Real-time** | WebSockets (FastAPI native) |
| **ML** | LightGBM, SHAP, H3, scikit-learn, pandas, pyarrow |
| **Deployment** | Vercel (frontend), Railway (backend), Supabase (DB), Docker Compose (self-hosted) |
| **Observability** | Sentry, Prometheus, OpenTelemetry, Loguru |

---

## Project Structure

```
Prajna/
├── frontend/               # React 19 + TypeScript SPA (Vite)
│   └── src/
│       ├── pages/          # Dashboard, Geospatial, Analytics, Reports, Admin, etc.
│       ├── components/     # Charts, Map, Dashboard widgets, UI primitives
│       ├── hooks/          # useRisk, useHotspots, useAnalytics
│       ├── store/          # Zustand (authStore, uiStore)
│       └── services/       # Supabase client, WebSocket
├── backend/                # FastAPI application
│   └── app/
│       ├── api/v1/         # REST endpoints: auth, risk, hotspots, analytics,
│       │                   #   explainability, reports, dashboard, admin
│       ├── core/           # Config, security, logging, exceptions
│       ├── database/       # SQLAlchemy models, async session
│       ├── middleware/      # Auth, audit log, rate limiting, request ID
│       ├── services/       # Business logic (risk, hotspot, analytics, reports, cache)
│       ├── repositories/   # DB access layer
│       ├── schemas/        # Pydantic request/response models
│       ├── ml_artifacts/   # Pre-computed ML outputs (read-only)
│       └── main.py         # App factory, lifespan, middleware stack
│   └── websocket/          # WebSocket dashboard endpoint
├── ml/                     # ML pipeline (train → export artifacts)
│   ├── src/
│   │   ├── models/         # RiskModel (LightGBM), HotspotModel (H3 + LightGBM)
│   │   ├── features/       # Temporal, spatial, feature builder
│   │   ├── explainability/ # SHAP analysis
│   │   ├── evaluation/     # TimeSeriesSplit CV, metrics
│   │   └── pipeline.py     # End-to-end pipeline orchestrator
│   ├── scripts/            # train.py, predict.py, export_to_backend.py
│   └── data/raw/           # crime_dataset_v2.csv / .parquet
├── database/               # SQL migrations, RLS policies, seeds, helper functions
├── deployment/             # Docker Compose, Nginx, Railway, Vercel configs
├── docs/                   # Architecture, API reference, deployment, user guide
└── .github/                # CI/CD workflows (ci, deploy, docker, lint)
```

---

## ML Pipeline

The `ml/` module is a self-contained pipeline that produces all artifacts consumed by the backend.

**Models:**
- **Risk Model** — LightGBM regressor predicting `Crime_Count_District`; outputs risk scores (0–100), priority rank, and confidence per district/month
- **Hotspot Model** — H3 spatial indexing + LightGBM; outputs ranked H3 cell predictions and a GeoJSON FeatureCollection
- **Explainability** — SHAP TreeExplainer; exports `feature_importance.csv`, `shap_values.parquet`, `explanation.json`
- **Analytics Engine** — Computes trends, seasonality, crime categories, neighbor influence; exports `analytics_report.json` and `dashboard_metrics.json`

**Validation:** TimeSeriesSplit (no data leakage). Train: 2021–2024 | Val: 2025 | Test: 2026.

**Run the pipeline:**
```bash
cd ml
pip install -r requirements.txt
python scripts/train.py
python scripts/predict.py
python scripts/export_to_backend.py   # copies artifacts to backend/app/ml_artifacts/
```

---

## Installation & Local Setup

### Prerequisites

- Node.js ≥ 20
- Python ≥ 3.11
- Redis (local or cloud)
- Supabase project
- Mapbox access token

### 1. Clone

```bash
git clone <repo-url>
cd Prajna
```

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in values
```

### 3. Frontend

```bash
cd frontend
npm install            # or: pnpm install
cp .env.example .env   # fill in values
```

### 4. Database

Run the SQL files in order via the Supabase SQL Editor:

```
database/migrations/0001_initial_schema.sql
database/policies/rls_policies.sql
database/functions/helper_functions.sql
database/seeds/001_default_admin.sql
```

See [`database/README.md`](database/README.md) for full setup instructions.

### 5. ML Artifacts

Either run the ML pipeline (see above) or place pre-computed artifacts in:

```
backend/app/ml_artifacts/
├── dashboard_metrics.json
├── analytics_report.json
├── predictions/
│   ├── predictions.csv
│   ├── hotspot_rankings.csv
│   └── hotspots.geojson
└── shap/
    └── explanation.json
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|---|---|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key |
| `SUPABASE_JWT_SECRET` | JWT secret from Supabase |
| `DATABASE_URL` | PostgreSQL async connection string |
| `REDIS_URL` | Redis connection URL |
| `ML_ARTIFACTS_PATH` | Path to ML artifacts directory |
| `SENTRY_DSN` | (Optional) Sentry DSN |

### Frontend (`frontend/.env`)

| Variable | Description |
|---|---|
| `VITE_API_BASE_URL` | Backend API base URL |
| `VITE_WS_BASE_URL` | WebSocket base URL |
| `VITE_SUPABASE_URL` | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon key |
| `VITE_MAPBOX_PUBLIC_TOKEN` | Mapbox public token |

---

## Running the Project

```bash
# Backend (terminal 1)
cd backend
uvicorn app.main:app --reload --port 8000

# Frontend (terminal 2)
cd frontend
npm run dev
```

- Frontend: [http://localhost:5173](http://localhost:5173)
- API docs (dev only): [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)

---

## API Overview

All endpoints are under `/api/v1/` and require JWT authentication (except `/auth`).

| Prefix | Description |
|---|---|
| `POST /auth/login` | Authenticate and receive JWT |
| `GET /risk/rankings` | All district risk rankings |
| `GET /risk/top` | Top N districts by risk score |
| `GET /risk/district/{district}` | Single district prediction |
| `GET /hotspots` | All hotspot rankings |
| `GET /hotspots/top` | Top N hotspots |
| `GET /hotspots/geojson` | GeoJSON FeatureCollection for map rendering |
| `GET /analytics` | Full analytics report |
| `GET /analytics/trends` | Crime trend analysis |
| `GET /analytics/seasonality` | Seasonal patterns |
| `GET /analytics/categories` | Crime category distribution |
| `GET /dashboard` | Dashboard KPIs and summary metrics |
| `GET /explainability` | SHAP feature importance |
| `POST /reports/generate` | Generate report (async) |
| `GET /reports/download/{id}` | Download report (PDF/CSV/JSON/GeoJSON) |
| `WS /ws/dashboard` | Real-time dashboard updates |

---

## Deployment

### Docker Compose (self-hosted)

```bash
cd deployment/docker
docker compose up --build
```

Services: `backend` (port 8000), `frontend` (port 80), `redis`.

### Vercel (frontend)

Config at `deployment/vercel/vercel.json`. Connect the `frontend/` directory to a Vercel project. Set all `VITE_*` environment variables in the Vercel dashboard.

### Railway (backend)

Config at `deployment/railway/railway.toml`. Set all backend environment variables in the Railway dashboard.

---

## User Roles

| Role | Access |
|---|---|
| **Admin** | Full access: manage users, view all reports, admin panel |
| **Officer** | View dashboards, generate reports, view hotspots |
| **Analyst** | View analytics, explainability, run ad-hoc reports |

---

## Documentation

- [Architecture Overview](docs/architecture/ARCHITECTURE.md)
- [API Reference](docs/api/API_REFERENCE.md)
- [Deployment Guide](docs/deployment/DEPLOYMENT.md)
- [User Guide](docs/user_guide/USER_GUIDE.md)
- [Database Schema](database/README.md)
- [ML Pipeline](ml/README.md)

---

## License

MIT License — see [LICENSE](LICENSE) for details.
