# 📊 Database — Supabase PostgreSQL

This directory contains all SQL migrations, RLS policies, and helper functions for the platform.

## 📁 Structure

```
database/
├── migrations/        # Sequential schema migrations
│   └── 0001_initial_schema.sql
├── policies/          # Row Level Security policies
│   └── rls_policies.sql
├── seeds/             # Initial data
│   └── 001_default_admin.sql
├── functions/         # Postgres helper functions
│   └── helper_functions.sql
└── README.md          # This file
```

## 🚀 Setup Instructions

### 1. Create a Supabase Project
1. Go to [https://supabase.com](https://supabase.com) and create a new project
2. Note the **Project URL**, **anon key**, **service_role key**, and **JWT secret**
3. Copy these into `backend/.env` and `frontend/.env`

### 2. Run Migrations
Execute SQL files in order using the Supabase SQL Editor or `psql`:

```bash
# Via Supabase SQL Editor: paste each file and run
# 1. migrations/0001_initial_schema.sql
# 2. policies/rls_policies.sql
# 3. functions/helper_functions.sql
# 4. seeds/001_default_admin.sql
```

### 3. Verify Setup
```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public';

-- Check RLS is enabled
SELECT tablename, rowsecurity FROM pg_tables
WHERE schemaname = 'public';
```

### 4. Create Your First Admin User
1. In Supabase Dashboard → **Authentication** → **Users** → **Add user**
2. Create the user with email + password
3. Copy the user's UUID
4. Update the seed record with the correct `supabase_user_id`:
   ```sql
   UPDATE users
   SET supabase_user_id = '<paste-uuid-here>'
   WHERE email = 'admin@crime-intel.gov';
   ```

## 🔒 Security

All tables have **Row Level Security (RLS)** enabled. Policies enforce:
- Users see only their own records
- Officers see all operational data
- Admins manage everything

Backend uses the **service_role key** to bypass RLS for system operations.

## 🧹 Maintenance

Schedule periodic cleanup (Supabase → Database → Cron Jobs):

```sql
-- Run daily
SELECT cleanup_expired_cache();
SELECT cleanup_expired_reports();
```
