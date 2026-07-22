-- ====================================================
-- Migration 0001: Initial Schema
-- ====================================================
-- Creates: users, saved_reports, audit_logs, dashboard_cache
-- ====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "postgis";  -- optional, for geo queries

-- ====================================================
-- ENUM types
-- ====================================================
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('admin', 'officer', 'analyst');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE user_status AS ENUM ('active', 'inactive', 'suspended', 'pending');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE report_type AS ENUM (
        'dashboard_summary', 'risk_ranking', 'hotspot_analysis',
        'district_deep_dive', 'analytics_report', 'explainability', 'custom'
    );
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE report_format AS ENUM ('csv', 'pdf', 'geojson', 'json');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE report_status AS ENUM (
        'pending', 'processing', 'completed', 'failed', 'expired'
    );
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE audit_action AS ENUM (
        'login', 'logout', 'login_failed', 'register', 'password_change',
        'create', 'read', 'update', 'delete',
        'report_generate', 'report_download', 'report_delete',
        'api_call', 'export',
        'user_create', 'user_update', 'user_delete', 'role_change',
        'cache_refresh', 'websocket_connect'
    );
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE cache_type AS ENUM (
        'metrics', 'risk_rankings', 'hotspots', 'analytics',
        'explainability', 'district_detail', 'full_dashboard'
    );
EXCEPTION WHEN duplicate_object THEN null; END $$;

-- ====================================================
-- users
-- ====================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supabase_user_id UUID UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    avatar_url TEXT,
    phone VARCHAR(50),
    role user_role NOT NULL DEFAULT 'analyst',
    status user_status NOT NULL DEFAULT 'active',
    department VARCHAR(255),
    badge_number VARCHAR(100),
    jurisdiction VARCHAR(255),
    preferences JSONB DEFAULT '{}'::jsonb,
    last_login_at TIMESTAMPTZ,
    last_login_ip VARCHAR(45),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_users_role ON users(role);
CREATE INDEX IF NOT EXISTS ix_users_status ON users(status);
CREATE INDEX IF NOT EXISTS ix_users_supabase_id ON users(supabase_user_id);
CREATE INDEX IF NOT EXISTS ix_users_created_at ON users(created_at DESC);

-- ====================================================
-- saved_reports
-- ====================================================
CREATE TABLE IF NOT EXISTS saved_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    report_type report_type NOT NULL,
    format report_format NOT NULL,
    status report_status NOT NULL DEFAULT 'pending',
    filters JSONB DEFAULT '{}'::jsonb,
    parameters JSONB DEFAULT '{}'::jsonb,
    file_path VARCHAR(1000),
    file_size BIGINT,
    file_hash VARCHAR(64),
    download_count BIGINT NOT NULL DEFAULT 0,
    error_message TEXT,
    retry_count BIGINT NOT NULL DEFAULT 0,
    generation_started_at TIMESTAMPTZ,
    generation_completed_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_saved_reports_user_id ON saved_reports(user_id);
CREATE INDEX IF NOT EXISTS ix_saved_reports_status ON saved_reports(status);
CREATE INDEX IF NOT EXISTS ix_saved_reports_type ON saved_reports(report_type);
CREATE INDEX IF NOT EXISTS ix_saved_reports_created_at ON saved_reports(created_at DESC);
CREATE INDEX IF NOT EXISTS ix_saved_reports_expires_at ON saved_reports(expires_at);

-- ====================================================
-- audit_logs (append-only)
-- ====================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    user_email VARCHAR(255),
    user_role VARCHAR(50),
    action audit_action NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    method VARCHAR(10),
    path VARCHAR(500),
    status_code INTEGER,
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(64),
    duration_ms INTEGER,
    extra_data JSONB DEFAULT '{}'::jsonb,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS ix_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS ix_audit_logs_request_id ON audit_logs(request_id);

-- ====================================================
-- dashboard_cache
-- ====================================================
CREATE TABLE IF NOT EXISTS dashboard_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key VARCHAR(500) UNIQUE NOT NULL,
    cache_type cache_type NOT NULL,
    payload JSONB NOT NULL,
    source VARCHAR(255),
    payload_size BIGINT,
    hit_count BIGINT NOT NULL DEFAULT 0,
    ttl_seconds INTEGER NOT NULL DEFAULT 300,
    expires_at TIMESTAMPTZ NOT NULL,
    last_refreshed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_dashboard_cache_type ON dashboard_cache(cache_type);
CREATE INDEX IF NOT EXISTS ix_dashboard_cache_expires ON dashboard_cache(expires_at);

-- ====================================================
-- updated_at trigger function
-- ====================================================
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach to tables with updated_at
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_updated_at_users') THEN
        CREATE TRIGGER set_updated_at_users BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_updated_at_saved_reports') THEN
        CREATE TRIGGER set_updated_at_saved_reports BEFORE UPDATE ON saved_reports
        FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_updated_at_dashboard_cache') THEN
        CREATE TRIGGER set_updated_at_dashboard_cache BEFORE UPDATE ON dashboard_cache
        FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
    END IF;
END $$;

-- ====================================================
-- Comments
-- ====================================================
COMMENT ON TABLE users IS 'User profiles, synced with Supabase auth.users';
COMMENT ON TABLE saved_reports IS 'User-generated reports (CSV, PDF, GeoJSON, JSON)';
COMMENT ON TABLE audit_logs IS 'Append-only audit trail of all system actions';
COMMENT ON TABLE dashboard_cache IS 'Pre-computed dashboard payloads for fast reads';
