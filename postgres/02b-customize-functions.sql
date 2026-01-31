-- ============================================================================
-- CUSTOMIZE FUNCTIONS - User-defined calculation functions
-- ============================================================================
-- This file is for YOUR custom PostgreSQL functions that should persist
-- across regeneration of the base ERB files.
--
-- USE THIS FILE FOR:
--   - Additional calc_* functions for computed fields
--   - Helper functions for complex business logic
--   - Utility functions for data transformation
--   - Trigger functions for custom automation
--
-- IMPORTANT:
--   - This file runs AFTER 02-create-functions.sql
--   - Base ERB calc functions already exist when this runs
--   - This file will NOT be overwritten by ERB regeneration
--   - Functions defined here can be used in 03b-customize-views.sql
--
-- ERB FUNCTION NAMING CONVENTIONS:
--   - calc_tablename_fieldname() - Returns a computed value for a view field
--   - Helper functions can use any naming convention
--
-- EXAMPLES:
--
--   -- Custom calculation function for a view field
--   CREATE OR REPLACE FUNCTION calc_orders_total_with_tax(p_order_id TEXT)
--   RETURNS NUMERIC AS $$
--   BEGIN
--       RETURN (SELECT subtotal * 1.08 FROM orders WHERE order_id = p_order_id);
--   END;
--   $$ LANGUAGE plpgsql STABLE;
--
--   -- Utility function
--   CREATE OR REPLACE FUNCTION format_currency(p_amount NUMERIC)
--   RETURNS TEXT AS $$
--   BEGIN
--       RETURN '$' || TO_CHAR(p_amount, 'FM999,999,990.00');
--   END;
--   $$ LANGUAGE plpgsql IMMUTABLE;
--
-- ============================================================================

/* This is a nuclear option to override the broken auto-generated version from 02-create-functions.sql */
/*
DO $$ 
DECLARE
    rec RECORD;
BEGIN
    FOR rec IN
        SELECT n.nspname as schema_name,
               p.proname as function_name,
               pg_catalog.pg_get_function_arguments(p.oid) as arguments
        FROM pg_catalog.pg_proc p
        LEFT JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'public'  -- assuming all functions are in the public schema
          AND n.nspname NOT IN ('pg_catalog', 'information_schema')
    LOOP
        EXECUTE format('DROP FUNCTION IF EXISTS %I.%I(%s) CASCADE', rec.schema_name, rec.function_name, rec.arguments);
    END LOOP;
END $$;
*/


-- Your custom functions go here:

-- Overrides the broken auto-generated version from 02-create-functions.sql
-- Formula: =COUNTIFS(OfficesHeld!{{Person}}, People!{{PersonId}}, OfficesHeld!{{OfficeName}}, "US Senator") > 0
CREATE OR REPLACE FUNCTION calc_people_has_ever_been_us_senator(p_person_id INTEGER)
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1
    FROM offices_held oh
    JOIN offices o ON oh.office = o.office_id
    WHERE oh.person = p_person_id
      AND o.name = 'US Senator'
  );
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- Overrides the broken auto-generated version from 02-create-functions.sql
-- Formula: =COUNTIFS(OfficesHeld!{{Person}}, People!{{PersonId}}, OfficesHeld!{{OfficeName}}, "US Senator")
CREATE OR REPLACE FUNCTION calc_people_senator_term_count(p_person_id INTEGER)
RETURNS INTEGER AS $$
BEGIN
  RETURN (
    SELECT COUNT(*)::INTEGER
    FROM offices_held oh
    JOIN offices o ON oh.office = o.office_id
    WHERE oh.person = p_person_id
      AND o.name = 'US Senator'
  );
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- INTEGER overload for calc_offices_holder_count
-- Formula: =COUNTIFS(OfficesHeld!{{Office}}, Offices!{{OfficeId}})
CREATE OR REPLACE FUNCTION calc_offices_holder_count(p_office_id INTEGER)
RETURNS INTEGER AS $$
BEGIN
  RETURN (SELECT COUNT(*)::INTEGER FROM offices_held WHERE office = p_office_id);
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- INTEGER overload for calc_states_resident_count
-- Formula: =COUNTIFS(PersonResidences!{{State}}, States!{{StateId}})
CREATE OR REPLACE FUNCTION calc_states_resident_count(p_state_id INTEGER)
RETURNS INTEGER AS $$
BEGIN
  RETURN (SELECT COUNT(*)::INTEGER FROM person_residences WHERE state = p_state_id);
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- INTEGER overload for calc_offices_held_person_name
-- Formula: =INDEX(People!{{Name}}, MATCH(OfficesHeld!{{Person}}, People!{{PersonId}}, 0))
CREATE OR REPLACE FUNCTION calc_offices_held_person_name(p_office_held_id INTEGER)
RETURNS TEXT AS $$
BEGIN
  RETURN (SELECT p.name FROM people p JOIN offices_held oh ON p.person_id = oh.person WHERE oh.office_held_id = p_office_held_id);
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- INTEGER overload for calc_offices_held_office_name
-- Formula: =INDEX(Offices!{{Name}}, MATCH(OfficesHeld!{{Office}}, Offices!{{OfficeId}}, 0))
CREATE OR REPLACE FUNCTION calc_offices_held_office_name(p_office_held_id INTEGER)
RETURNS TEXT AS $$
BEGIN
  RETURN (SELECT o.name FROM offices o JOIN offices_held oh ON o.office_id = oh.office WHERE oh.office_held_id = p_office_held_id);
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- INTEGER overload for calc_offices_held_district_name
-- Formula: =INDEX(States!{{Name}}, MATCH(OfficesHeld!{{District}}, States!{{StateId}}, 0))
CREATE OR REPLACE FUNCTION calc_offices_held_district_name(p_office_held_id INTEGER)
RETURNS TEXT AS $$
BEGIN
  RETURN (SELECT s.name FROM states s JOIN offices_held oh ON s.state_id = oh.district WHERE oh.office_held_id = p_office_held_id);
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- INTEGER overload for calc_offices_held_district_abbreviation
-- Formula: =INDEX(States!{{Abbreviation}}, MATCH(OfficesHeld!{{District}}, States!{{StateId}}, 0))
CREATE OR REPLACE FUNCTION calc_offices_held_district_abbreviation(p_office_held_id INTEGER)
RETURNS TEXT AS $$
BEGIN
  RETURN (SELECT s.abbreviation FROM states s JOIN offices_held oh ON s.state_id = oh.district WHERE oh.office_held_id = p_office_held_id);
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- INTEGER overload for calc_offices_held_term_duration_days
-- Formula: =DATEDIFF({{EndDate}}, {{StartDate}})
CREATE OR REPLACE FUNCTION calc_offices_held_term_duration_days(p_office_held_id INTEGER)
RETURNS INTEGER AS $$
BEGIN
  RETURN (SELECT (end_date - start_date)::INTEGER FROM offices_held WHERE office_held_id = p_office_held_id);
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- INTEGER overload for calc_person_residences_person_name
-- Formula: =INDEX(People!{{Name}}, MATCH(PersonResidences!{{Person}}, People!{{PersonId}}, 0))
CREATE OR REPLACE FUNCTION calc_person_residences_person_name(p_residence_id INTEGER)
RETURNS TEXT AS $$
BEGIN
  RETURN (SELECT p.name FROM people p JOIN person_residences pr ON p.person_id = pr.person WHERE pr.residence_id = p_residence_id);
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- INTEGER overload for calc_person_residences_state_name
-- Formula: =INDEX(States!{{Name}}, MATCH(PersonResidences!{{State}}, States!{{StateId}}, 0))
CREATE OR REPLACE FUNCTION calc_person_residences_state_name(p_residence_id INTEGER)
RETURNS TEXT AS $$
BEGIN
  RETURN (SELECT s.name FROM states s JOIN person_residences pr ON s.state_id = pr.state WHERE pr.residence_id = p_residence_id);
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- INTEGER overload for calc_person_residences_state_abbreviation
-- Formula: =INDEX(States!{{Abbreviation}}, MATCH(PersonResidences!{{State}}, States!{{StateId}}, 0))
CREATE OR REPLACE FUNCTION calc_person_residences_state_abbreviation(p_residence_id INTEGER)
RETURNS TEXT AS $$
BEGIN
  RETURN (SELECT s.abbreviation FROM states s JOIN person_residences pr ON s.state_id = pr.state WHERE pr.residence_id = p_residence_id);
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- Aggregates all offices_held records for a person as comma-separated list of IDs
-- RelatedTo: OfficesHeld
CREATE OR REPLACE FUNCTION calc_people_offices_held_list(p_person_id INTEGER)
RETURNS TEXT AS $$
BEGIN
  RETURN (
    SELECT STRING_AGG(office_held_id::TEXT, ', ' ORDER BY start_date)
    FROM offices_held
    WHERE person = p_person_id
  );
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- Aggregates all person_residences records for a person as comma-separated list of IDs
-- RelatedTo: PersonResidences
CREATE OR REPLACE FUNCTION calc_people_residences_list(p_person_id INTEGER)
RETURNS TEXT AS $$
BEGIN
  RETURN (
    SELECT STRING_AGG(residence_id::TEXT, ', ' ORDER BY start_date)
    FROM person_residences
    WHERE person = p_person_id
  );
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;