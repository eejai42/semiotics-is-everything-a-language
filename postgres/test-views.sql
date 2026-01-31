-- ============================================================================
-- TEST VIEWS - Query each vw_* view and report failures
-- ============================================================================
-- Run with: psql postgresql://postgres@localhost:5432/effortless-demo -f test-views.sql
-- ============================================================================

\echo ''
\echo '============================================================'
\echo '  VIEW TEST REPORT'
\echo '============================================================'
\echo ''

-- Create temp table to track results
CREATE TEMP TABLE view_test_results (
    view_name TEXT,
    status TEXT,
    row_count INTEGER,
    error_message TEXT
);

-- Test vw_books
DO $$
BEGIN
    PERFORM * FROM vw_books LIMIT 1;
    INSERT INTO view_test_results VALUES ('vw_books', 'PASS', (SELECT COUNT(*) FROM vw_books), NULL);
EXCEPTION WHEN OTHERS THEN
    INSERT INTO view_test_results VALUES ('vw_books', 'FAIL', NULL, SQLERRM);
END $$;

-- Test vw_lendings
DO $$
BEGIN
    PERFORM * FROM vw_lendings LIMIT 1;
    INSERT INTO view_test_results VALUES ('vw_lendings', 'PASS', (SELECT COUNT(*) FROM vw_lendings), NULL);
EXCEPTION WHEN OTHERS THEN
    INSERT INTO view_test_results VALUES ('vw_lendings', 'FAIL', NULL, SQLERRM);
END $$;

-- Test vw_locations
DO $$
BEGIN
    PERFORM * FROM vw_locations LIMIT 1;
    INSERT INTO view_test_results VALUES ('vw_locations', 'PASS', (SELECT COUNT(*) FROM vw_locations), NULL);
EXCEPTION WHEN OTHERS THEN
    INSERT INTO view_test_results VALUES ('vw_locations', 'FAIL', NULL, SQLERRM);
END $$;

-- Test vw_erb_versions
DO $$
BEGIN
    PERFORM * FROM vw_erb_versions LIMIT 1;
    INSERT INTO view_test_results VALUES ('vw_erb_versions', 'PASS', (SELECT COUNT(*) FROM vw_erb_versions), NULL);
EXCEPTION WHEN OTHERS THEN
    INSERT INTO view_test_results VALUES ('vw_erb_versions', 'FAIL', NULL, SQLERRM);
END $$;

-- Test vw_erb_customizations
DO $$
BEGIN
    PERFORM * FROM vw_erb_customizations LIMIT 1;
    INSERT INTO view_test_results VALUES ('vw_erb_customizations', 'PASS', (SELECT COUNT(*) FROM vw_erb_customizations), NULL);
EXCEPTION WHEN OTHERS THEN
    INSERT INTO view_test_results VALUES ('vw_erb_customizations', 'FAIL', NULL, SQLERRM);
END $$;

-- Test vw_airtable_attachments
DO $$
BEGIN
    PERFORM * FROM vw_airtable_attachments LIMIT 1;
    INSERT INTO view_test_results VALUES ('vw_airtable_attachments', 'PASS', (SELECT COUNT(*) FROM vw_airtable_attachments), NULL);
EXCEPTION WHEN OTHERS THEN
    INSERT INTO view_test_results VALUES ('vw_airtable_attachments', 'FAIL', NULL, SQLERRM);
END $$;

-- Display summary
\echo '  SUMMARY'
\echo '  -------'
SELECT
    '  ' ||
    CASE status WHEN 'PASS' THEN '✓' ELSE '✗' END || ' ' ||
    view_name ||
    CASE WHEN status = 'PASS' THEN ' (' || row_count || ' rows)' ELSE '' END AS result
FROM view_test_results;

\echo ''
\echo '  STATISTICS'
\echo '  ----------'
SELECT
    '  Total: ' || COUNT(*) ||
    ' | Passed: ' || COUNT(*) FILTER (WHERE status = 'PASS') ||
    ' | Failed: ' || COUNT(*) FILTER (WHERE status = 'FAIL') AS summary
FROM view_test_results;

-- Show failures with details
\echo ''
\echo '============================================================'
\echo '  FAILURE DETAILS'
\echo '============================================================'

DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN SELECT * FROM view_test_results WHERE status = 'FAIL'
    LOOP
        RAISE NOTICE '';
        RAISE NOTICE '  VIEW: %', r.view_name;
        RAISE NOTICE '  ERROR: %', r.error_message;

        -- Provide diagnosis based on error message
        IF r.error_message LIKE '%function sum(timestamp%)%' THEN
            RAISE NOTICE '  CAUSE: A calc function uses SUM() on a timestamp column';
            RAISE NOTICE '         SUM only works on numeric types. Use MAX() for latest date.';
        ELSIF r.error_message LIKE '%function sum(text)%' THEN
            RAISE NOTICE '  CAUSE: A calc function uses SUM() on a text column';
            RAISE NOTICE '         SUM only works on numeric types. Use STRING_AGG() for text.';
        ELSIF r.error_message LIKE '%COALESCE types%cannot be matched%' THEN
            RAISE NOTICE '  CAUSE: COALESCE used with incompatible types (e.g., timestamp and boolean)';
            RAISE NOTICE '         Use "IS NOT NULL" instead of COALESCE with FALSE for null checks.';
        ELSIF r.error_message LIKE '%does not exist%' THEN
            RAISE NOTICE '  CAUSE: Missing function or object referenced in view';
        ELSE
            RAISE NOTICE '  CAUSE: Unknown - manual investigation required';
        END IF;
    END LOOP;

    IF NOT EXISTS (SELECT 1 FROM view_test_results WHERE status = 'FAIL') THEN
        RAISE NOTICE '';
        RAISE NOTICE '  All views passed - no failures to report.';
    END IF;
END $$;

\echo ''
\echo '============================================================'
\echo '  TEST COMPLETE'
\echo '============================================================'
\echo ''

DROP TABLE view_test_results;
