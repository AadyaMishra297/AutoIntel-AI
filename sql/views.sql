

CREATE VIEW Repair_View AS
SELECT
    o.OBD_Code,
    o.Description,
    o.Category,
    o.Severity,
    o.Severity_Level,
    o.Primary_System,
    rk.Repair_Priority,
    rk.Estimated_Repair_Cost_Min_INR,
    rk.Estimated_Repair_Cost_Max_INR,
    rk.Estimated_Labor_Hours_Min,
    rk.Estimated_Labor_Hours_Max
FROM Repair_Knowledge rk
JOIN OBD_Codes o ON rk.OBD_Code = o.OBD_Code;

CREATE VIEW Vehicle_View AS
SELECT
    Vehicle_ID,
    vehicle_model,
    Brand,
    Model,
    Variant,
    fuel_type,
    engine_size,
    Engine,
    Manufacturing_Year
FROM Vehicle_Master;

-- Picks the latest service record PER vehicle using a correlated
-- subquery. If a vehicle has a genuine tie (two records on the same
-- latest date), both are returned rather than arbitrarily dropped.
CREATE VIEW Latest_Maintenance_View AS
SELECT vm.*
FROM Vehicle_Maintenance vm
WHERE vm.last_service_date = (
    SELECT MAX(vm2.last_service_date)
    FROM Vehicle_Maintenance vm2
    WHERE vm2.Vehicle_ID = vm.Vehicle_ID
);

-- IMPORTANT: this view has no natural FK between vehicles and OBD
-- codes (the code is predicted by the NLP layer at query time, not
-- stored). The join below is deliberately a cross join — ALWAYS
-- filter by both Vehicle_ID and OBD_Code when querying this view,
-- or you'll get every vehicle x every OBD code (180 x 7387 rows).
CREATE VIEW Diagnosis_View AS
SELECT
    v.Vehicle_ID,
    v.Brand,
    v.Model,
    v.Manufacturing_Year,
    lm.Vehicle_Health_Score,
    lm.Maintenance_Risk_Level,
    lm.last_service_date,
    rv.OBD_Code,
    rv.Description AS Fault_Description,
    rv.Severity,
    rv.Repair_Priority,
    rv.Estimated_Repair_Cost_Min_INR,
    rv.Estimated_Repair_Cost_Max_INR,
    rv.Estimated_Labor_Hours_Min,
    rv.Estimated_Labor_Hours_Max
FROM Vehicle_Master v
JOIN Latest_Maintenance_View lm ON v.Vehicle_ID = lm.Vehicle_ID
JOIN Repair_View rv ON 1 = 1;

-- Verify: should list all four views
SELECT name FROM sqlite_master WHERE type = 'view';

-- Example safe usage of Diagnosis_View — must always include both filters
-- SELECT * FROM Diagnosis_View WHERE Vehicle_ID = 'VEH0001' AND OBD_Code = 'P0001';
