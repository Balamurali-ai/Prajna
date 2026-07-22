-- ====================================================
-- Supabase Helper Functions
-- ====================================================

-- Function: get current user's role
CREATE OR REPLACE FUNCTION get_user_role(uid UUID)
RETURNS TEXT AS $$
    SELECT role::text FROM users WHERE supabase_user_id = uid AND is_deleted = false;
$$ LANGUAGE SQL STABLE;

-- Function: is current user admin
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM users
        WHERE supabase_user_id = auth.uid()
        AND role = 'admin'
        AND is_deleted = false
    );
$$ LANGUAGE SQL STABLE;

-- Function: is current user officer or above
CREATE OR REPLACE FUNCTION is_officer_or_above()
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM users
        WHERE supabase_user_id = auth.uid()
        AND role IN ('admin', 'officer')
        AND is_deleted = false
    );
$$ LANGUAGE SQL STABLE;

-- Function: cleanup expired cache
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM dashboard_cache WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function: cleanup expired reports
CREATE OR REPLACE FUNCTION cleanup_expired_reports()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    UPDATE saved_reports
    SET status = 'expired'
    WHERE expires_at < NOW() AND status IN ('completed', 'pending', 'processing');
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
