# 🏗️ Architecture Overview

## High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Browser (React 19 SPA)                       │
│   Vite + TS + Tailwind + ShadCN + React Query + Zustand         │
│   Mapbox GL JS (geospatial)  •  Recharts (analytics)            │
└───────────────┬─────────────────────────────────────┬─────────────┘
                │ HTTPS / WSS                         │ HTTPS
                ▼                                     ▼
┌────────────────────────┐         ┌──────────────────────────────┐
│  Vercel Edge / CDN     │         │  Railway (FastAPI Backend)   │
│  (Static SPA hosting)  │         │  Python 3.12 + Uvicorn       │
└────────────────────────┘         │  + 4 workers (gunicorn)      │
                                   └──────┬────────────────┬──────┘
                                          │                │
                                          ▼                ▼
                              ┌─────────────────┐  ┌──────────────────┐
                              │ Supabase        │  │ Redis            │
                              │ (Postgres +     │  │ (cache + rate    │
                              │  Auth + RLS)    │  │  limiting)       │
                              └─────────────────┘  └──────────────────┘
                                          ▲
                                          │ (read-only)
                              ┌───────────┴────────────┐
                              │  ML Artifacts          │
                              │  (CSV/JSON/Parquet)    │
                              │  Owned by ML team      │
                              └────────────────────────┘
```

## Folder Structure

```
crime-intelligence-platform/
├── frontend/              # React 19 + Vite SPA
│   ├── src/
│   │   ├── api/          # HTTP client + endpoints
│   │   ├── components/   # ShadCN UI + custom components
│   │   │   ├── ui/       # Button, Card, Badge, Input, ...
│   │   │   ├── layout/   # Sidebar, Topbar, AppLayout
│   │   │   ├── dashboard/# KPICard, Tables, AlertsPanel
│   │   │   ├── map/      # MapView, MapLegend (Mapbox)
│   │   │   └── charts/   # Trend, Category, SHAP (Recharts)
│   │   ├── hooks/        # React Query hooks
│   │   ├── pages/        # Route-level components
│   │   ├── store/        # Zustand stores (auth, UI)
│   │   ├── services/     # Supabase, WebSocket
│   │   ├── types/        # TypeScript domain types
│   │   ├── utils/        # Formatters, helpers
│   │   ├── routes/       # React Router config
│   │   ├── config/       # Env-driven config
│   │   └── styles/       # Tailwind globals
│   ├── public/           # Static assets
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── Dockerfile
│   ├── nginx.conf
│   └── .env.example
│
├── backend/               # FastAPI
│   ├── app/
│   │   ├── api/v1/        # Versioned endpoints
│   │   │   └── endpoints/ # dashboard, risk, hotspots, ...
│   │   ├── core/          # config, logging, security, exceptions
│   │   ├── services/      # Business logic + ML loader
│   │   ├── repositories/  # SQLAlchemy data access
│   │   ├── schemas/       # Pydantic models
│   │   ├── middleware/    # auth, audit, rate-limit, request-id
│   │   ├── websocket/     # /ws/dashboard
│   │   ├── database/      # session, models
│   │   ├── utils/         # formatters, geo helpers
│   │   └── main.py        # App factory
│   ├── tests/             # pytest
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── Dockerfile
│   └── .env.example
│
├── database/              # SQL migrations + RLS
│   ├── migrations/        # *.sql (numbered)
│   ├── policies/          # rls_policies.sql
│   ├── seeds/             # default admin, etc.
│   ├── functions/         # Postgres helper functions
│   └── README.md
│
├── deployment/            # Ops configs
│   ├── docker/            # docker-compose.yml
│   ├── railway/           # railway.toml, railway.json
│   ├── vercel/            # vercel.json
│   └── scripts/           # Helper scripts
│
├── docs/                  # Documentation
│   ├── api/               # API reference
│   ├── architecture/      # This file
│   ├── deployment/        # Deploy guides
│   └── user-guide/        # End-user docs
│
├── .github/               # CI/CD
│   ├── workflows/         # ci.yml, deploy.yml, lint.yml, docker.yml
│   └── ISSUE_TEMPLATE/
│
├── README.md              # Project root
├── LICENSE
├── package.json           # Workspace root (concurrent dev)
├── .env.example
└── .gitignore
```

## Data Flow

1. **ML Pipeline** (separate repo) writes artifacts to `backend/app/ml_artifacts/`
2. **FastAPI** starts → `MLArtifactLoader` reads all artifacts into memory
3. **REST API** serves them to the frontend
4. **WebSocket** pushes real-time updates when artifacts change
5. **React SPA** fetches data via React Query, renders in components
6. **Supabase** stores user data, reports, audit logs (with RLS)
7. **Redis** caches hot endpoints and rate-limits per IP

## Roles & Permissions

| Role | Capabilities |
|---|---|
| **Admin** | All endpoints + user management |
| **Officer** | All read endpoints + report generation |
| **Analyst** | All read endpoints + own reports |

Enforced via:
- Backend middleware (FastAPI dependencies)
- Database RLS policies (Supabase)

## Caching Strategy

| Layer | TTL | Scope |
|---|---|---|
| Browser (React Query) | 60s | All GETs |
| Backend (Redis) | 300s | Dashboard, rankings, hotspots |
| Backend (in-memory) | 900s | ML artifacts |
| HTTP (CDN) | 1y | Static assets |
