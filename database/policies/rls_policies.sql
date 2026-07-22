-- ====================================================
-- Migration 0002: Row Level Security (RLS)
-- ====================================================
-- Enable RLS on all tables and define policies.
-- Assumes Supabase JWT contains a 'sub' = user UUID and 'role' claim.
-- ====================================================

-- ====================================================
-- Enable RLS
-- ====================================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE dashboard_cache ENABLE ROW LEVEL SECURITY;

-- ====================================================
-- users policies
-- ====================================================
-- Users can read their own profile
DROP POLICY IF EXISTS "Users can view own profile" ON users;
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT
    USING (auth.uid() = supabase_user_id);

-- Users can update their own profile (limited fields enforced in app)
DROP POLICY IF EXISTS "Users can update own profile" ON users;
CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE
    USING (auth.uid() = supabase_user_id);

-- Admins can do everything on users
DROP POLICY IF EXISTS "Admins can manage all users" ON users;
CREATE POLICY "Admins can manage all users" ON users
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM users u
            WHERE u.supabase_user_id = auth.uid()
            AND u.role = 'admin'
            AND u.is_deleted = false
        )
    );

-- Officers can view all users (read-only)
DROP POLICY IF EXISTS "Officers can view all users" ON users;
CREATE POLICY "Officers can view all users" ON users
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users u
            WHERE u.supabase_user_id = auth.uid()
            AND u.role IN ('admin', 'officer')
            AND u.is_deleted = false
        )
    );

-- ====================================================
-- saved_reports policies
-- ====================================================
-- Users can view their own reports
DROP POLICY IF EXISTS "Users can view own reports" ON saved_reports;
CREATE POLICY "Users can view own reports" ON saved_reports
    FOR SELECT
    USING (
        user_id IN (
            SELECT id FROM users WHERE supabase_user_id = auth.uid()
        )
    );

-- Users can create their own reports
DROP POLICY IF EXISTS "Users can create own reports" ON saved_reports;
CREATE POLICY "Users can create own reports" ON saved_reports
    FOR INSERT
    WITH CHECK (
        user_id IN (
            SELECT id FROM users WHERE supabase_user_id = auth.uid()
        )
    );

-- Users can delete their own reports
DROP POLICY IF EXISTS "Users can delete own reports" ON saved_reports;
CREATE POLICY "Users can delete own reports" ON saved_reports
    FOR DELETE
    USING (
        user_id IN (
            SELECT id FROM users WHERE supabase_user_id = auth.uid()
        )
    );

-- Admins can view all reports
DROP POLICY IF EXISTS "Admins can view all reports" ON saved_reports;
CREATE POLICY "Admins can view all reports" ON saved_reports
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users u
            WHERE u.supabase_user_id = auth.uid()
            AND u.role = 'admin'
        )
    );

-- Officers can view all reports
DROP POLICY IF EXISTS "Officers can view all reports" ON saved_reports;
CREATE POLICY "Officers can view all reports" ON saved_reports
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users u
            WHERE u.supabase_user_id = auth.uid()
            AND u.role IN ('admin', 'officer')
        )
    );

-- ====================================================
-- audit_logs policies
-- ====================================================
-- Users can view their own audit log
DROP POLICY IF EXISTS "Users can view own audit" ON audit_logs;
CREATE POLICY "Users can view own audit" ON audit_logs
    FOR SELECT
    USING (
        user_id IN (
            SELECT id FROM users WHERE supabase_user_id = auth.uid()
        )
    );

-- Only admins can view all audit logs
DROP POLICY IF EXISTS "Admins can view all audit" ON audit_logs;
CREATE POLICY "Admins can view all audit" ON audit_logs
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users u
            WHERE u.supabase_user_id = auth.uid()
            AND u.role = 'admin'
        )
    );

-- Service role inserts audit logs (backend uses service_role key)
-- No INSERT policy for regular users

-- ====================================================
-- dashboard_cache policies
-- ====================================================
-- All authenticated users can read dashboard cache
DROP POLICY IF EXISTS "Authenticated users can read cache" ON dashboard_cache;
CREATE POLICY "Authenticated users can read cache" ON dashboard_cache
    FOR SELECT
    TO authenticated
    USING (true);

-- Only service role can write to cache
-- (No INSERT/UPDATE/DELETE policies for regular users)
