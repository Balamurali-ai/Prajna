# 📡 API Reference

Base URL: `https://api.crime-intel.example.com/api/v1`

All endpoints (except auth) require a Bearer token in the `Authorization` header.

## Authentication

Obtain a token from Supabase Auth (frontend) or `POST /auth/login` (backend dev).

```
Authorization: Bearer <jwt_token>
```

## Endpoints

### Health

```
GET /health
```

Returns service status. No auth required.

### Dashboard

```
GET /api/v1/dashboard
```
Returns the complete dashboard payload in a single call:
- KPI metrics
- Top 10 districts
- Top 10 hotspots
- Active alerts

### Risk

```
GET /api/v1/risk/rankings            # All districts
GET /api/v1/risk/top10               # Top 10
GET /api/v1/risk/top?n=20            # Top N
GET /api/v1/risk/district/{name}     # Single district
```

### Hotspots

```
GET /api/v1/hotspots                 # All rankings
GET /api/v1/hotspots/top?n=50        # Top N
GET /api/v1/hotspots/geojson         # GeoJSON FeatureCollection
```

### Analytics

```
GET /api/v1/analytics                # Full report
GET /api/v1/analytics/trends         # Trend analysis
GET /api/v1/analytics/seasonality    # Seasonal patterns
GET /api/v1/analytics/categories     # Crime distribution
GET /api/v1/analytics/neighbor-influence
```

### Explainability

```
GET /api/v1/explainability/global              # SHAP global
GET /api/v1/explainability/district/{name}     # Per-district SHAP
```

### Reports

```
POST /api/v1/reports/generate                  # Queue generation
GET  /api/v1/reports                           # List my reports
GET  /api/v1/reports/{id}                      # Status
GET  /api/v1/reports/download/{id}             # Download file
DELETE /api/v1/reports/{id}                    # Delete
```

### Auth

```
POST /api/v1/auth/login
POST /api/v1/auth/register    (admin)
GET  /api/v1/auth/me
POST /api/v1/auth/change-password
```

### Admin

```
GET    /api/v1/admin/users
GET    /api/v1/admin/users/{id}
PATCH  /api/v1/admin/users/{id}
DELETE /api/v1/admin/users/{id}
```

## WebSocket

```
WS /ws/dashboard
```

Channels:
- `risk_rankings`
- `hotspots`
- `reports`
- `alerts`

Message types: `risk_update`, `hotspot_update`, `report_complete`, `heartbeat`.

## Error Format

```json
{
  "success": false,
  "error": {
    "code": "not_found",
    "message": "District not found",
    "details": { "district": "Atlantis" }
  },
  "request_id": "uuid"
}
```

| Code | HTTP |
|---|---|
| `not_found` | 404 |
| `unauthenticated` | 401 |
| `forbidden` | 403 |
| `validation_error` | 422 |
| `rate_limited` | 429 |
| `ml_artifact_unavailable` | 503 |
| `internal_error` | 500 |
