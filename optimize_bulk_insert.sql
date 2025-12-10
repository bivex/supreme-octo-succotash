-- PostgreSQL Bulk Insert Optimizations
-- Execute these commands before bulk INSERT operations

-- 1. Temporarily disable indexes for better INSERT performance
-- WARNING: This will make SELECT queries slower during the operation
-- Only use for bulk inserts, then recreate indexes

-- Disable specific indexes that slow down INSERT (optional, use with caution)
/*
ALTER INDEX idx_events_click_id ATTACH PARTITION ... ; -- If using partitioning
-- OR temporarily drop indexes:
DROP INDEX IF EXISTS idx_events_click_id;
DROP INDEX IF EXISTS idx_events_type;
DROP INDEX IF EXISTS idx_events_created_at;
*/

-- 2. Increase maintenance_work_mem for faster index creation (if recreating indexes)
-- SET maintenance_work_mem = '256MB';

-- 3. Use bulk INSERT with proper transaction management
-- Example of optimized bulk insert:

BEGIN;

-- Disable autovacuum temporarily for this session
SET autovacuum_enabled = false;

-- Use COPY for maximum performance (if loading from file)
/*
COPY events (id, click_id, event_type, event_data, created_at)
FROM '/path/to/data.csv'
WITH (FORMAT csv, HEADER true);
*/

-- Or optimized multi-row INSERT
INSERT INTO events (id, click_id, event_type, event_data, created_at)
VALUES
    (gen_random_uuid()::text, 'click_1', 'page_view', '{"url": "/home"}', NOW()),
    (gen_random_uuid()::text, 'click_2', 'click', '{"element": "button"}', NOW()),
    -- ... more rows
ON CONFLICT DO NOTHING; -- Avoid duplicate key errors

COMMIT;

-- 4. Re-enable autovacuum
SET autovacuum_enabled = true;

-- 5. Recreate indexes if they were dropped
/*
CREATE INDEX CONCURRENTLY idx_events_click_id ON events (click_id);
CREATE INDEX CONCURRENTLY idx_events_type ON events (event_type);
CREATE INDEX CONCURRENTLY idx_events_created_at ON events (created_at DESC);
*/

-- 6. Run ANALYZE to update statistics
ANALYZE events;

-- 7. Monitor performance improvement
SELECT
    schemaname,
    relname as table_name,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes
FROM pg_stat_user_tables
WHERE relname = 'events';
