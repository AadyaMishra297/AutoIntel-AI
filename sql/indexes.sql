-- ============================================================
-- AutoIntel AI — Indexes
-- Run this AFTER validation.sql passes clean.
--
-- Note: SQLite auto-indexes every PRIMARY KEY (Vehicle_ID, OBD_Code,
-- Maintenance_ID) already — these are additional indexes on foreign
-- keys and columns used in WHERE/JOIN/ORDER BY across queries.sql
-- and views.sql.
-- ============================================================

-- FK column — every JOIN from Vehicle_Maintenance to Vehicle_Master
-- filters on this; without it, SQLite scans all 50,000 rows per JOIN.
CREATE INDEX idx_maintenance_vehicle_id ON Vehicle_Maintenance(Vehicle_ID);

-- Common lookup/filter columns from Step 8 query patterns
CREATE INDEX idx_maintenance_last_service_date ON Vehicle_Maintenance(last_service_date);
CREATE INDEX idx_maintenance_risk_level ON Vehicle_Maintenance(Maintenance_Risk_Level);
CREATE INDEX idx_obd_severity ON OBD_Codes(Severity_Level);
CREATE INDEX idx_repair_priority ON Repair_Knowledge(Repair_Priority);

-- Composite index for "latest maintenance per vehicle" pattern:
-- WHERE Vehicle_ID = ? ORDER BY last_service_date DESC
-- Satisfies both the filter and the sort from one index.
CREATE INDEX idx_maintenance_vehicle_date ON Vehicle_Maintenance(Vehicle_ID, last_service_date);

-- Verify: should list all 6 named indexes above
SELECT name, tbl_name FROM sqlite_master WHERE type = 'index' AND name NOT LIKE 'sqlite_%';

-- Optional: confirm SQLite is actually using the composite index
-- (output should say "USING INDEX idx_maintenance_vehicle_date", not "SCAN")
EXPLAIN QUERY PLAN
SELECT * FROM Vehicle_Maintenance WHERE Vehicle_ID = 'VEH0001' ORDER BY last_service_date DESC;
