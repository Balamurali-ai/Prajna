# 🛡️ Geospatial Crime Pattern Intelligence Platform

> **Police Command-Center Dashboard for Crime Intelligence, Risk Rankings, Hotspot Visualization, and Explainability**

[![ET AI Hackathon 2026](https://img.shields.io/badge/Hackathon-ET%20AI%202026-blue)](#)
[![License](https://img.shields.io/badge/license-MIT-green)](#)
[![Frontend](https://img.shields.io/badge/Frontend-React%2019-61dafb)](#)
[![Backend](https://img.shields.io/badge/Backend-FastAPI-009688)](#)
[![Database](https://img.shields.io/badge/Database-Supabase-3ecf8e)](#)

---

## 🎯 Overview

The **Geospatial Crime Pattern Intelligence Platform** is a production-grade command-center dashboard built for the **ET AI Hackathon 2026**. It ingests pre-computed outputs from an existing ML pipeline and presents crime intelligence, risk rankings, geospatial hotspots, and SHAP-based explainability to police command staff.

### ⚠️ ML Scope Boundary

| Layer | Owner | Scope |
|---|---|---|
| **ML / Data Science** | Other Team | ✅ Predictions, SHAP, Feature Engineering |
| **Backend / Frontend / DB / API** | **This Team** | ✅ FastAPI, React, Supabase, Deployment |

**This repository contains ZERO ML training or prediction code.** It only reads ML outputs (CSVs, JSON, GeoJSON, Parquet) and serves them via REST/WebSocket APIs.

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 19, TypeScript, Vite, TailwindCSS, ShadCN UI, React Query, Zustand, Recharts, Mapbox GL JS |
| **Backend** | FastAPI, SQLAlchemy 2.0, Pydantic v2, Redis, Uvicorn |
| **Database** | Supabase PostgreSQL with RLS |
| **Auth** | Supabase Auth (JWT, RBAC) |
| **Real-time** | WebSockets (FastAPI native) |
| **Deployment** | Vercel (frontend), Railway (backend), Supabase (DB) |

---

## 📂 Repository Structure

```
crime-intelligence-platform/
├── frontend/         # React 19 + TypeScript SPA
├── backend/          # FastAPI application
├── database/         # SQL migrations, RLS, seeds
├── deployment/       # Docker, Railway, Vercel configs
├── docs/             # Architecture, API, deployment guides
└── .github/          # CI/CD workflows
```

---

## 🚀 Quick Start

### Prerequisites

- Node.js ≥ 20.x
- Python ≥ 3.11
- pnpm or npm
- Supabase account
- Mapbox access token

### 1. Clone & Install

```bash
git clone <repo-url>
cd crime-intelligence-platform

# Backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Frontend
cd ../frontend && pnpm install
cp .env.example .env
```

### 2. ML Outputs Placement

Place the ML-generated artifacts in `backend/app/ml_artifacts/`:

```
backend/app/ml_artifacts/
├── predictions/
│   ├── predictions.csv
│   ├── hotspot_rankings.csv
│   └── hotspots.geojson
├── dashboard_metrics.json
├── analytics_report.json
├── feature_importance.csv
└── shap/
    └── shap_values.parquet
```

### 3. Run Locally

```bash
# Backend (terminal 1)
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend (terminal 2)
cd frontend && pnpm dev
```

Open [http://localhost:5173](http://localhost:5173) for the dashboard.

---

## 👥 User Roles

| Role | Capabilities |
|---|---|
| **Admin** | Full access: manage users, view all reports, regenerate caches |
| **Officer** | View all dashboards, generate reports, view hotspots |
| **Analyst** | View analytics, run ad-hoc reports, view explainability |

---

## 📖 Documentation

- [Architecture Overview](docs/architecture/ARCHITECTURE.md)
- [API Reference](docs/api/API_REFERENCE.md)
- [Deployment Guide](docs/deployment/DEPLOYMENT.md)
- [User Guide](docs/user-guide/USER_GUIDE.md)
- [Database Schema](database/README.md)

---

## 🏆 Competition

Built for **ET AI Hackathon 2026** — a production-grade command-center platform that turns ML predictions into actionable police intelligence.

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.
