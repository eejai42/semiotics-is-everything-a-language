-- ============================================================================
-- MagicAuth Superuser Installation Script (Crypto Layer)
-- ============================================================================
--
-- PURPOSE: Sets up the JWT verification infrastructure that requires:
--   1. Superuser privileges (for plpython3u - untrusted language)
--   2. PyJWT/cryptography Python packages on the PostgreSQL server
--
-- RUN THIS: Once per tenant database, as superuser (e.g., postgres)
--
-- AFTER THIS: Run tenant-install.sql as the tenant user to set up
--             the RLS layer (no superuser or crypto library needed)
--
-- Prerequisites:
--   pip install pyjwt cryptography
--
-- ============================================================================

-- Create auth schema
CREATE SCHEMA IF NOT EXISTS auth;

-- Enable plpython3u extension (REQUIRES SUPERUSER)
-- The 'u' suffix means "untrusted" - can execute arbitrary Python code
CREATE EXTENSION IF NOT EXISTS plpython3u;

-- ============================================================================
-- TRUSTED TENANTS TABLE
-- ============================================================================
-- Stores the public key for JWT verification
-- Each tenant database has one row with their RSA public key

CREATE TABLE IF NOT EXISTS auth.trusted_tenants (
    tenant_id TEXT PRIMARY KEY,
    public_key_pem TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE auth.trusted_tenants IS
    'Stores tenant public keys for RS256 JWT verification. '
    'Register your public key here after obtaining it from MagicAuth.';

-- ============================================================================
-- JWT VERIFICATION FUNCTION (RS256 via PL/Python)
-- ============================================================================
-- This is the ONLY function that requires crypto libraries.
-- It verifies the JWT signature and expiration using the tenant's public key.
--
-- Returns: verified claims as JSONB if valid
-- Raises: exception if invalid (malformed, expired, bad signature, unknown tenant)

CREATE OR REPLACE FUNCTION auth.verify_jwt(token TEXT)
RETURNS JSONB
LANGUAGE plpython3u
SECURITY DEFINER
AS $$
import json

# Validate input
if not token:
    plpy.error('JWT token is required')

# First, decode without verification to get tenant_id
try:
    import jwt
    unverified = jwt.decode(token, options={"verify_signature": False})
except Exception as e:
    plpy.error(f'Malformed JWT: {str(e)}')

tenant_id = unverified.get('tenant_id')
if not tenant_id:
    plpy.error('JWT missing tenant_id claim')

# Look up tenants public key from trusted_tenants (use prepared statement for safety)
plan = plpy.prepare("SELECT public_key_pem FROM auth.trusted_tenants WHERE tenant_id = $1", ["text"])
result = plpy.execute(plan, [tenant_id])

if len(result) == 0:
    plpy.error(f'Unknown tenant: {tenant_id}')

public_key = result[0]['public_key_pem']

# Verify the JWT with the public key
try:
    # PyJWT automatically verifies signature and expiration
    verified = jwt.decode(
        token,
        public_key,
        algorithms=['RS256'],
        options={
            "require": ["exp", "iat", "tenant_id", "email"],
            "verify_exp": True,
            "verify_iat": True
        }
    )
    return json.dumps(verified)
except jwt.ExpiredSignatureError:
    plpy.error('JWT has expired')
except jwt.InvalidSignatureError:
    plpy.error('Invalid JWT signature')
except jwt.InvalidTokenError as e:
    plpy.error(f'Invalid JWT: {str(e)}')
$$;

COMMENT ON FUNCTION auth.verify_jwt(TEXT) IS
    'Verifies JWT signature using tenant public key and checks expiration. '
    'Returns claims as JSONB if valid, raises exception if invalid. '
    'This is the only function requiring PyJWT/cryptography.';

-- ============================================================================
-- USAGE
-- ============================================================================
--
-- 1. Run this script as superuser:
--    psql -U postgres -d your_tenant_db -f trusted-superuser-install.sql
--
-- 2. Register your tenant's public key:
--    INSERT INTO auth.trusted_tenants (tenant_id, public_key_pem)
--    VALUES (
--        'your-tenant-uuid',
--        '-----BEGIN PUBLIC KEY-----
--    MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
--    -----END PUBLIC KEY-----'
--    );
--
-- 3. Run tenant-install.sql as the tenant user to set up RLS functions
--
-- ============================================================================
