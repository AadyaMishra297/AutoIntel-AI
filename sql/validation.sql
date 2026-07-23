
SELECT COUNT(*) AS null_vehicle_id FROM Vehicle_Master WHERE Vehicle_ID IS NULL;
SELECT COUNT(*) AS null_obd_code FROM OBD_Codes WHERE OBD_Code IS NULL;
SELECT COUNT(*) AS null_repair_obd_code FROM Repair_Knowledge WHERE OBD_Code IS NULL;
SELECT COUNT(*) AS null_maintenance_id FROM Vehicle_Maintenance WHERE Maintenance_ID IS NULL;

-- 6.2 Null Foreign Keys — expect 0 in both results
SELECT COUNT(*) AS null_fk_vehicle_id FROM Vehicle_Maintenance WHERE Vehicle_ID IS NULL;
SELECT COUNT(*) AS null_fk_obd_code FROM Repair_Knowledge WHERE OBD_Code IS NULL;

-- 6.3 Orphan Foreign Keys — expect zero rows returned from both queries
-- (SQLite does not enforce FK constraints by default, so this must
-- be checked explicitly rather than assumed.)
SELECT vm.Vehicle_ID, COUNT(*) AS orphan_count
FROM Vehicle_Maintenance vm
LEFT JOIN Vehicle_Master v ON vm.Vehicle_ID = v.Vehicle_ID
WHERE v.Vehicle_ID IS NULL
GROUP BY vm.Vehicle_ID;

SELECT rk.OBD_Code, COUNT(*) AS orphan_count
FROM Repair_Knowledge rk
LEFT JOIN OBD_Codes o ON rk.OBD_Code = o.OBD_Code
WHERE o.OBD_Code IS NULL
GROUP BY rk.OBD_Code;

-- 6.4 Duplicate Primary Keys — expect zero rows from all four
SELECT Vehicle_ID, COUNT(*) FROM Vehicle_Master GROUP BY Vehicle_ID HAVING COUNT(*) > 1;
SELECT OBD_Code, COUNT(*) FROM OBD_Codes GROUP BY OBD_Code HAVING COUNT(*) > 1;
SELECT OBD_Code, COUNT(*) FROM Repair_Knowledge GROUP BY OBD_Code HAVING COUNT(*) > 1;
SELECT Maintenance_ID, COUNT(*) FROM Vehicle_Maintenance GROUP BY Maintenance_ID HAVING COUNT(*) > 1;

-- 6.5 Date column sanity checks
-- Format consistency — expect a single row each with len = 10 (YYYY-MM-DD)
SELECT DISTINCT LENGTH(last_service_date) AS len, COUNT(*)
FROM Vehicle_Maintenance
GROUP BY len;

SELECT DISTINCT LENGTH(warranty_expiry_date) AS len, COUNT(*)
FROM Vehicle_Maintenance
GROUP BY len;

-- Confirm dates parse correctly (parsed_ok should be a large numeric value, never NULL)
SELECT last_service_date, julianday(last_service_date) AS parsed_ok
FROM Vehicle_Maintenance
LIMIT 5;

-- Range sanity check — years should look realistic, not corrupted
SELECT MIN(last_service_date), MAX(last_service_date) FROM Vehicle_Maintenance;
SELECT MIN(warranty_expiry_date), MAX(warranty_expiry_date) FROM Vehicle_Maintenance;

-- 6.6 Spot-check imported values against source CSV
SELECT * FROM Vehicle_Master WHERE Vehicle_ID = 'VEH0001';

-- Confirm column types imported correctly (numeric columns should show
-- INTEGER/REAL, not TEXT)
PRAGMA table_info(Vehicle_Maintenance);

-- Row count summary — expect 180 / 7387 / 50000 / 7387
SELECT
    (SELECT COUNT(*) FROM Vehicle_Master)       AS vehicle_master,
    (SELECT COUNT(*) FROM OBD_Codes)            AS obd_codes,
    (SELECT COUNT(*) FROM Vehicle_Maintenance)  AS vehicle_maintenance,
    (SELECT COUNT(*) FROM Repair_Knowledge)     AS repair_knowledge;
