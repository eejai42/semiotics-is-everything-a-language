

-- ============================================================================
-- MagicAuth Permissions Template
-- ============================================================================
--
-- PURPOSE: Grants permissions to a tenant user to run tenant-install.sql
--          and use the auth functions.
--
-- USAGE:
--   1. Find/replace these placeholders with your actual values:
--      YOUR_DATABASE_NAME  ->  your tenant database name
--      app7SvujNpwcfUNKN_cc7519a298_user    ->  the PostgreSQL role for your tenant
--
--   2. Run this script as superuser AFTER running trusted-superuser-install.sql
--
-- ============================================================================

-- ============================================================================
-- DATABASE-LEVEL PERMISSIONS
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS "auth";

-- Allow tenant user to create objects in the database
GRANT CREATE ON DATABASE "app7SvujNpwcfUNKN_cc7519a298" TO "app7SvujNpwcfUNKN_cc7519a298_user";

-- ============================================================================
-- SCHEMA PERMISSIONS
-- ============================================================================

-- Grant usage and create rights on public schema
GRANT USAGE ON SCHEMA public TO "app7SvujNpwcfUNKN_cc7519a298_user";
GRANT CREATE ON SCHEMA public TO "app7SvujNpwcfUNKN_cc7519a298_user";

-- Grant usage on auth schema (created by superuser install)
GRANT USAGE ON SCHEMA auth TO "app7SvujNpwcfUNKN_cc7519a298_user";
GRANT CREATE ON SCHEMA auth TO "app7SvujNpwcfUNKN_cc7519a298_user";

-- ============================================================================
-- OBJECT PERMISSIONS
-- ============================================================================

-- Grant privileges on existing objects in public schema
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "app7SvujNpwcfUNKN_cc7519a298_user";
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "app7SvujNpwcfUNKN_cc7519a298_user";
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO "app7SvujNpwcfUNKN_cc7519a298_user";

-- Grant privileges on existing objects in auth schema
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA auth TO "app7SvujNpwcfUNKN_cc7519a298_user";
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA auth TO "app7SvujNpwcfUNKN_cc7519a298_user";
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA auth TO "app7SvujNpwcfUNKN_cc7519a298_user";

-- ============================================================================
-- DEFAULT PRIVILEGES (for future objects)
-- ============================================================================

-- Ensure tenant user has access to future objects in public schema
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL PRIVILEGES ON TABLES TO "app7SvujNpwcfUNKN_cc7519a298_user";

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL PRIVILEGES ON SEQUENCES TO "app7SvujNpwcfUNKN_cc7519a298_user";

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT EXECUTE ON FUNCTIONS TO "app7SvujNpwcfUNKN_cc7519a298_user";

-- Ensure tenant user has access to future objects in auth schema
ALTER DEFAULT PRIVILEGES IN SCHEMA auth
GRANT ALL PRIVILEGES ON TABLES TO "app7SvujNpwcfUNKN_cc7519a298_user";

ALTER DEFAULT PRIVILEGES IN SCHEMA auth
GRANT ALL PRIVILEGES ON SEQUENCES TO "app7SvujNpwcfUNKN_cc7519a298_user";

ALTER DEFAULT PRIVILEGES IN SCHEMA auth
GRANT EXECUTE ON FUNCTIONS TO "app7SvujNpwcfUNKN_cc7519a298_user";

-- ============================================================================
-- LANGUAGE PERMISSIONS
-- ============================================================================

-- Grant usage on plpgsql (standard procedural language)
GRANT USAGE ON LANGUAGE plpgsql TO "app7SvujNpwcfUNKN_cc7519a298_user";

-- Note: plpython3u usage is handled by SECURITY DEFINER on verify_jwt
-- Tenant user does NOT need direct plpython3u access

-- ============================================================================
-- USAGE EXAMPLE
-- ============================================================================
--
-- For a database named "myapp_prod" and user "myapp_user":
--
--   sed 's/YOUR_DATABASE_NAME/myapp_prod/g; s/app7SvujNpwcfUNKN_cc7519a298_user/myapp_user/g' \
--       permissions-template.sql | psql -U postgres
--
-- Or manually replace and run:
--   psql -U postgres -d myapp_prod -f permissions-template.sql
--
-- ============================================================================
