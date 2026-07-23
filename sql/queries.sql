
SELECT
    o.OBD_Code,
    o.Description,
    o.Category,
    o.Severity,
    rk.Repair_Priority,
    rk.Estimated_Repair_Cost_Min_INR,
    rk.Estimated_Repair_Cost_Max_INR,
    rk.Estimated_Labor_Hours_Min,
    rk.Estimated_Labor_Hours_Max
FROM Repair_Knowledge rk
JOIN OBD_Codes o ON rk.OBD_Code = o.OBD_Code
WHERE rk.OBD_Code = 'P0001';

-- 8.2 OBD Lookup — pure diagnostic meaning, no cost data
SELECT
    OBD_Code, Description, Category, Severity,
    Severity_Level, Fault_Description, Work_Required, Primary_System
FROM OBD_Codes
WHERE OBD_Code = 'P0001';

-- 8.3 Vehicle Information Lookup
SELECT
    Vehicle_ID, vehicle_model, Brand, Model, Variant,
    fuel_type, engine_size, Engine, Manufacturing_Year
FROM Vehicle_Master
WHERE Vehicle_ID = 'VEH0001';

-- 8.4 Maintenance History Lookup — full timeline, most recent first
SELECT
    Maintenance_ID, last_service_date, maintenance_history, reported_issues,
    service_history, accident_history, Vehicle_Health_Score, Maintenance_Risk_Level
FROM Vehicle_Maintenance
WHERE Vehicle_ID = 'VEH0001'
ORDER BY last_service_date DESC;

-- 8.5 Latest Maintenance Lookup — current status snapshot only
SELECT *
FROM Vehicle_Maintenance
WHERE Vehicle_ID = 'VEH0001'
ORDER BY last_service_date DESC
LIMIT 1;

-- 8.6 Combined Diagnosis Query — vehicle identity + current health + fault/repair detail
SELECT
    v.Vehicle_ID, v.Brand, v.Model, v.Manufacturing_Year,
    vm.Vehicle_Health_Score, vm.Maintenance_Risk_Level, vm.last_service_date,
    o.OBD_Code, o.Description AS Fault_Description, o.Severity,
    rk.Repair_Priority, rk.Estimated_Repair_Cost_Min_INR, rk.Estimated_Repair_Cost_Max_INR,
    rk.Estimated_Labor_Hours_Min, rk.Estimated_Labor_Hours_Max
FROM Vehicle_Master v
JOIN Vehicle_Maintenance vm ON v.Vehicle_ID = vm.Vehicle_ID
JOIN OBD_Codes o ON o.OBD_Code = 'P0001'
JOIN Repair_Knowledge rk ON rk.OBD_Code = o.OBD_Code
WHERE v.Vehicle_ID = 'VEH0001'
ORDER BY vm.last_service_date DESC
LIMIT 1;

-- 8.7 Fault Summary Query — system-wide aggregate for a trends dashboard
SELECT
    o.Category,
    o.Severity,
    COUNT(*) AS code_count,
    ROUND(AVG(rk.Estimated_Repair_Cost_Min_INR), 2) AS avg_min_cost_inr,
    ROUND(AVG(rk.Estimated_Repair_Cost_Max_INR), 2) AS avg_max_cost_inr
FROM OBD_Codes o
JOIN Repair_Knowledge rk ON o.OBD_Code = rk.OBD_Code
GROUP BY o.Category, o.Severity
ORDER BY code_count DESC;

-- Equivalent view-based versions (once views.sql has been run) —
-- prefer these in application code since the JOIN logic lives in one place:
-- SELECT * FROM Repair_View WHERE OBD_Code = 'P0001';
-- SELECT * FROM Latest_Maintenance_View WHERE Vehicle_ID = 'VEH0001';
-- SELECT * FROM Diagnosis_View WHERE Vehicle_ID = 'VEH0001' AND OBD_Code = 'P0001';
