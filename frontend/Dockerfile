# ====================================================
# Frontend Dockerfile (multi-stage build)
# ====================================================

# ---------- Stage 1: Build ----------
FROM node:20-alpine AS build

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install --no-audit --no-fund

# Copy source
COPY . .

# Build
ARG VITE_API_BASE_URL
ARG VITE_WS_BASE_URL
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY
ARG VITE_MAPBOX_PUBLIC_TOKEN

ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_WS_BASE_URL=$VITE_WS_BASE_URL
ENV VITE_SUPABASE_URL=$VITE_SUPABASE_URL
ENV VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_KEY
ENV VITE_MAPBOX_PUBLIC_TOKEN=$VITE_MAPBOX_PUBLIC_TOKEN

RUN npm run build

# ---------- Stage 2: Runtime (Nginx) ----------
FROM nginx:1.27-alpine AS runtime

LABEL maintainer="ET AI Hackathon Team"

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --spider --quiet http://localhost:80/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
