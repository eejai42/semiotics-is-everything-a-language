-- ============================================================================
-- MagicAuth Tenant Installation Script (RLS Layer)
-- ============================================================================
--
-- PURPOSE: Sets up the RLS infrastructure that links authenticated emails
--          to your application's user/role system.
--
-- REQUIREMENTS:
--   - trusted-superuser-install.sql must be run first (by superuser)
--   - NO superuser privileges needed for this script
--   - NO crypto libraries needed
--
-- AFTER THIS:
--   1. Register your tenant's public key in auth.trusted_tenants
--   2. Create your app_users table with: email_address, role, is_active
--   3. Call auth.set_jwt() at the start of each request
--   4. Use auth.email(), auth.role(), etc. in your RLS policies
--
-- ============================================================================

-- ============================================================================
-- RLS CONFIGURATION
-- ============================================================================
-- Controls whether JWT claims are scoped to transaction or session level

CREATE TABLE IF NOT EXISTS auth.rls_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Default: session-level enforcement (claims persist until cleared)
INSERT INTO auth.rls_config (key, value, description)
VALUES ('enforcement_level', 'session',
        'RLS claim scope: "transaction" (safer, clears on commit/rollback) or "session" (persists until cleared)')
ON CONFLICT (key) DO NOTHING;

-- ============================================================================
-- ENFORCEMENT LEVEL FUNCTIONS
-- ============================================================================

-- Get the current enforcement level setting
-- Returns TRUE for transaction-local, FALSE for session-level
CREATE OR REPLACE FUNCTION auth.is_transaction_local()
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
AS $$
    SELECT COALESCE(
        -- First check for session-level override via GUC
        CASE
            WHEN current_setting('auth.enforcement_override', true) = 'session' THEN FALSE
            WHEN current_setting('auth.enforcement_override', true) = 'transaction' THEN TRUE
            ELSE NULL  -- No override, use table setting
        END,
        -- Fall back to table configuration
        (SELECT value = 'transaction' FROM auth.rls_config WHERE key = 'enforcement_level'),
        -- Ultimate default: transaction-local (safest)
        TRUE
    );
$$;

COMMENT ON FUNCTION auth.is_transaction_local() IS
    'Returns TRUE if claims should be transaction-local, FALSE for session-level. '
    'Can be overridden per-session with: SET auth.enforcement_override = ''session''';

-- Set enforcement level for current session only (does not affect table default)
CREATE OR REPLACE FUNCTION auth.set_enforcement_level(level TEXT)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    IF level NOT IN ('transaction', 'session') THEN
        RAISE EXCEPTION 'enforcement_level must be "transaction" or "session"';
    END IF;
    PERFORM set_config('auth.enforcement_override', level, false);  -- false = session-level
END;
$$;

COMMENT ON FUNCTION auth.set_enforcement_level(TEXT) IS
    'Override RLS enforcement level for current session. Use "transaction" or "session".';

-- Update the persistent default enforcement level (affects all new sessions)
CREATE OR REPLACE FUNCTION auth.set_default_enforcement_level(level TEXT)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    IF level NOT IN ('transaction', 'session') THEN
        RAISE EXCEPTION 'enforcement_level must be "transaction" or "session"';
    END IF;

    UPDATE auth.rls_config
    SET value = level, updated_at = now()
    WHERE key = 'enforcement_level';

    IF NOT FOUND THEN
        INSERT INTO auth.rls_config (key, value, description)
        VALUES ('enforcement_level', level,
                'RLS claim scope: "transaction" (safer) or "session" (persists until cleared)');
    END IF;
END;
$$;

COMMENT ON FUNCTION auth.set_default_enforcement_level(TEXT) IS
    'Set the persistent default RLS enforcement level for all sessions.';

-- Get current enforcement level info
CREATE OR REPLACE FUNCTION auth.get_enforcement_level()
RETURNS TABLE(current_level TEXT, source TEXT, is_transaction_local BOOLEAN)
LANGUAGE sql
STABLE
AS $$
    SELECT
        CASE WHEN auth.is_transaction_local() THEN 'transaction' ELSE 'session' END,
        CASE
            WHEN current_setting('auth.enforcement_override', true) IN ('session', 'transaction')
                THEN 'session_override'
            ELSE 'database_default'
        END,
        auth.is_transaction_local();
$$;

COMMENT ON FUNCTION auth.get_enforcement_level() IS
    'Returns the current enforcement level, its source, and the boolean flag used by set_config.';

-- ============================================================================
-- JWT HELPER FUNCTIONS
-- ============================================================================

-- Decode JWT payload without verification (for debugging only)
-- WARNING: Do not trust this output for authorization - always use auth.verify_jwt
CREATE OR REPLACE FUNCTION auth.decode_jwt_payload_unsafe(token TEXT)
RETURNS JSONB
LANGUAGE sql
IMMUTABLE
STRICT
AS $$
    SELECT convert_from(
        decode(
            rpad(
                translate((string_to_array(token, '.'))[2], '-_', '+/'),
                4 * ceil(length((string_to_array(token, '.'))[2]) / 4.0)::int,
                '='
            ),
            'base64'
        ),
        'UTF8'
    )::jsonb;
$$;

COMMENT ON FUNCTION auth.decode_jwt_payload_unsafe(TEXT) IS
    'Decodes JWT payload WITHOUT signature verification. Never use for authorization.';

-- ============================================================================
-- SESSION CLAIMS MANAGEMENT
-- ============================================================================

-- Set session claims from a verified JWT
-- This is the main entry point - call this at the start of each request
CREATE OR REPLACE FUNCTION auth.set_jwt(token TEXT)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    claims JSONB;
    u RECORD;
    is_local BOOLEAN;
BEGIN
    -- Get configured enforcement level
    is_local := auth.is_transaction_local();

    -- Verify JWT and get claims (calls the crypto layer)
    claims := auth.verify_jwt(token);

    -- Set base claims from JWT
    PERFORM set_config('request.jwt.claim.email', claims->>'email', is_local);
    PERFORM set_config('request.jwt.claim.tenant_id', claims->>'tenant_id', is_local);
    PERFORM set_config('request.jwt.claim.sub', claims->>'sub', is_local);
    PERFORM set_config('request.jwt.claim.iss', claims->>'iss', is_local);
    PERFORM set_config('request.jwt.claim.iat', claims->>'iat', is_local);
    PERFORM set_config('request.jwt.claim.exp', claims->>'exp', is_local);

    -- =========================================================================
    -- EMAIL -> APP_USERS -> ROLE LINKAGE
    -- =========================================================================
    -- This is the tenant-specific part: map the authenticated email
    -- to your application's user/role system

    SELECT * INTO u
    FROM app_users
    WHERE email_address = claims->>'email'
      AND is_active = true;

    IF FOUND THEN
        PERFORM set_config('request.jwt.claim.role', u.role, is_local);
        PERFORM set_config('request.jwt.claim.is_registered', 'true', is_local);
    ELSE
        -- User authenticated via email but not in app_users
        -- Set flag so application can handle registration
        PERFORM set_config('request.jwt.claim.role', '', is_local);
        PERFORM set_config('request.jwt.claim.is_registered', 'false', is_local);
    END IF;
END;
$$;

COMMENT ON FUNCTION auth.set_jwt(TEXT) IS
    'Validates JWT and sets session claims for use in RLS policies. '
    'Links email to app_users table to determine role. Call at start of each request.';

-- Clear session claims (call at end of request or on error)
CREATE OR REPLACE FUNCTION auth.clear_jwt()
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    is_local BOOLEAN;
BEGIN
    is_local := auth.is_transaction_local();

    PERFORM set_config('request.jwt.claim.email', '', is_local);
    PERFORM set_config('request.jwt.claim.tenant_id', '', is_local);
    PERFORM set_config('request.jwt.claim.role', '', is_local);
    PERFORM set_config('request.jwt.claim.sub', '', is_local);
    PERFORM set_config('request.jwt.claim.iss', '', is_local);
    PERFORM set_config('request.jwt.claim.iat', '', is_local);
    PERFORM set_config('request.jwt.claim.exp', '', is_local);
    PERFORM set_config('request.jwt.claim.is_registered', '', is_local);
END;
$$;

COMMENT ON FUNCTION auth.clear_jwt() IS
    'Clears all JWT session claims. Call at end of request for connection pooling.';

-- ============================================================================
-- CLAIM GETTER FUNCTIONS
-- ============================================================================
-- Use these in RLS policies and application queries

CREATE OR REPLACE FUNCTION auth.email()
RETURNS TEXT
LANGUAGE sql
STABLE
AS $$
    SELECT nullif(current_setting('request.jwt.claim.email', true), '');
$$;

CREATE OR REPLACE FUNCTION auth.role()
RETURNS TEXT
LANGUAGE sql
STABLE
AS $$
    SELECT nullif(current_setting('request.jwt.claim.role', true), '');
$$;

CREATE OR REPLACE FUNCTION auth.tenant_id()
RETURNS TEXT
LANGUAGE sql
STABLE
AS $$
    SELECT nullif(current_setting('request.jwt.claim.tenant_id', true), '');
$$;

CREATE OR REPLACE FUNCTION auth.is_registered()
RETURNS BOOLEAN
LANGUAGE sql
STABLE
AS $$
    SELECT current_setting('request.jwt.claim.is_registered', true) = 'true';
$$;

COMMENT ON FUNCTION auth.email() IS 'Returns authenticated user email from JWT';
COMMENT ON FUNCTION auth.role() IS 'Returns authenticated user role (NULL if not registered in app_users)';
COMMENT ON FUNCTION auth.tenant_id() IS 'Returns tenant_id from JWT';
COMMENT ON FUNCTION auth.is_registered() IS 'Returns true if authenticated user exists in app_users';

-- ============================================================================
-- CONVENIENCE FUNCTIONS
-- ============================================================================

-- Check if user has a specific role
CREATE OR REPLACE FUNCTION auth.has_role(required_role TEXT)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
AS $$
    SELECT auth.role() = required_role;
$$;

-- Check if user has any of the specified roles
CREATE OR REPLACE FUNCTION auth.has_any_role(VARIADIC roles TEXT[])
RETURNS BOOLEAN
LANGUAGE sql
STABLE
AS $$
    SELECT auth.role() = ANY(roles);
$$;

-- Get the authenticated user's record from app_users
CREATE OR REPLACE FUNCTION auth.current_user_record()
RETURNS app_users
LANGUAGE sql
STABLE
SECURITY DEFINER
AS $$
    SELECT * FROM app_users
    WHERE email_address = auth.email()
    LIMIT 1;
$$;

-- ============================================================================
-- SCHEMA COMMENTS
-- ============================================================================

COMMENT ON SCHEMA auth IS 'MagicAuth JWT validation and session management';

-- ============================================================================
-- EXAMPLE: APP_USERS TABLE
-- ============================================================================
--
-- Your app_users table needs at minimum these columns:
--
--   CREATE TABLE app_users (
--       app_user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--       email_address TEXT UNIQUE NOT NULL,
--       role TEXT NOT NULL DEFAULT 'user',
--       is_active BOOLEAN NOT NULL DEFAULT true,
--       created_at TIMESTAMPTZ DEFAULT now()
--   );
--
-- ============================================================================
-- EXAMPLE: RLS POLICIES
-- ============================================================================
--
-- Users can only see their own data:
--
--   CREATE POLICY user_isolation ON my_table
--       FOR ALL
--       USING (email_address = auth.email());
--
-- Admin can see everything:
--
--   CREATE POLICY admin_access ON my_table
--       FOR ALL
--       USING (auth.has_role('admin'));
--
-- ============================================================================
-- EXAMPLE: CLIENT USAGE
-- ============================================================================
--
--   BEGIN;
--   SELECT auth.set_jwt('eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...');
--
--   -- Now RLS policies can use auth.* functions
--   SELECT * FROM my_table;
--
--   -- Check if user is registered
--   SELECT auth.is_registered();  -- returns false for new users
--
--   -- Register new user if needed
--   INSERT INTO app_users (email_address, role)
--   VALUES (auth.email(), 'user')
--   ON CONFLICT (email_address) DO NOTHING;
--
--   COMMIT;
--
-- ============================================================================
-- EXAMPLE: CONFIGURING ENFORCEMENT LEVEL
-- ============================================================================
--
--   - TRANSACTION (safer): Claims are cleared on COMMIT/ROLLBACK
--   - SESSION: Claims persist until explicitly cleared
--
-- Check current level:
--   SELECT * FROM auth.get_enforcement_level();
--
-- Override for current session:
--   SELECT auth.set_enforcement_level('session');
--
-- Change database default:
--   SELECT auth.set_default_enforcement_level('transaction');
--
-- ============================================================================
