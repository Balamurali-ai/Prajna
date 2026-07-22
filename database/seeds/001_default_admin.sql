-- ====================================================
-- Seed: Default Admin User
-- ====================================================
-- Insert a default admin user record.
-- The actual auth is handled by Supabase; this is just the profile.
-- ====================================================
-- Replace the UUID below with the actual Supabase user ID for the admin.
-- This is a placeholder — you should update after creating the user in Supabase.

INSERT INTO users (
    id,
    supabase_user_id,
    email,
    full_name,
    role,
    status,
    department,
    badge_number,
    created_at,
    updated_at,
    is_deleted
) VALUES (
    '00000000-0000-0000-0000-000000000001'::uuid,
    '00000000-0000-0000-0000-000000000001'::uuid,
    'admin@crime-intel.gov',
    'System Administrator',
    'admin',
    'active',
    'Command Center',
    'ADMIN-001',
    NOW(),
    NOW(),
    false
)
ON CONFLICT (email) DO NOTHING;

-- Note: In production, after creating the admin in Supabase Auth,
-- run an UPDATE to set the supabase_user_id to match.
