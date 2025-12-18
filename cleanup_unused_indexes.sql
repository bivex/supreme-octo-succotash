-- Script to identify and optionally drop unused indexes
-- Run this script to find indexes that haven't been used since the last stats reset

-- First, let's see unused indexes (indexes with 0 scans)
SELECT schemaname,
       relname                                      as table_name,
       indexrelname                                 as index_name,
       idx_scan,
       pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
       pg_get_indexdef(indexrelid)                  as index_definition
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;

-- To drop unused indexes, uncomment and modify the following template:
-- Note: Be careful! Monitor application performance after dropping indexes
/*
DROP INDEX IF EXISTS public.index_name_here;
*/

-- Alternative: Reset statistics to start fresh monitoring
-- SELECT pg_stat_reset();

/*
-- Example of dropping some unused indexes (customize based on your needs):
-- These are the largest unused indexes from our audit:

-- Large unused indexes that can be safely removed:
DROP INDEX IF EXISTS public.idx_ltv_segments_min_ltv;
DROP INDEX IF EXISTS public.idx_customer_ltv_dates;
DROP INDEX IF EXISTS public.idx_customer_ltv_cohort;
DROP INDEX IF EXISTS public.idx_customer_ltv_segment;
DROP INDEX IF EXISTS public.idx_cohorts_acquisition;
DROP INDEX IF EXISTS public.idx_churn_probability;
DROP INDEX IF EXISTS public.idx_churn_risk;

-- Form submission indexes (if not used by application):
-- DROP INDEX IF EXISTS public.idx_submissions_form;
-- DROP INDEX IF EXISTS public.idx_submissions_ip;
-- DROP INDEX IF EXISTS public.idx_submissions_email;
-- DROP INDEX IF EXISTS public.idx_submissions_date;

-- Lead indexes (if not used):
-- DROP INDEX IF EXISTS public.idx_leads_email;
-- DROP INDEX IF EXISTS public.idx_leads_status;
-- DROP INDEX IF EXISTS public.idx_leads_source;
-- DROP INDEX IF EXISTS public.idx_leads_created;
*/
