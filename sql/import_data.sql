

-- 1. Vehicle_Master (straight copy)
INSERT INTO Vehicle_Master (
    Vehicle_ID, vehicle_model, Brand, Model, Variant,
    fuel_type, engine_size, Engine, Manufacturing_Year
)
SELECT
    Vehicle_ID, vehicle_model, Brand, Model, Variant,
    fuel_type, engine_size, Engine, Manufacturing_Year
FROM staging_vehicle_master;

-- 2. OBD_Codes (straight copy)
INSERT INTO OBD_Codes (
    OBD_Code, Description, Category, Severity,
    Fault_Description, Work_Required, Severity_Level, Primary_System
)
SELECT
    OBD_Code, Description, Category, Severity,
    Fault_Description, Work_Required, Severity_Level, Primary_System
FROM staging_obd_codes;

-- 3. Vehicle_Maintenance — Maintenance_ID deliberately omitted so
-- SQLite autoincrements it instead of pulling from the CSV.
INSERT INTO Vehicle_Maintenance (
    Vehicle_ID, vehicle_model, mileage, maintenance_history, reported_issues,
    vehicle_age, fuel_type, transmission_type, engine_size, odometer_reading,
    last_service_date, warranty_expiry_date, owner_type, insurance_premium,
    service_history, accident_history, fuel_efficiency, tire_condition,
    brake_condition, battery_status, need_maintenance, Months_Since_Last_Service,
    Warranty_Status, Warranty_Remaining_Months, Odometer_Category,
    Fuel_Efficiency_Rating, Annual_Mileage, Vehicle_Usage_Category,
    Service_Due_Status, Component_Wear_Score, Issue_Rate,
    Vehicle_Health_Score, Maintenance_Risk_Level
)
SELECT
    Vehicle_ID, vehicle_model, mileage, maintenance_history, reported_issues,
    vehicle_age, fuel_type, transmission_type, engine_size, odometer_reading,
    last_service_date, warranty_expiry_date, owner_type, insurance_premium,
    service_history, accident_history, fuel_efficiency, tire_condition,
    brake_condition, battery_status, need_maintenance, Months_Since_Last_Service,
    Warranty_Status, Warranty_Remaining_Months, Odometer_Category,
    Fuel_Efficiency_Rating, Annual_Mileage, Vehicle_Usage_Category,
    Service_Due_Status, Component_Wear_Score, Issue_Rate,
    Vehicle_Health_Score, Maintenance_Risk_Level
FROM staging_vehicle_maintenance;

-- 4. Repair_Knowledge — Description, Category, Severity, Severity_Level,
-- Primary_System, Work_Required deliberately dropped: they belong to
-- OBD_Codes and are retrieved via JOIN (see queries.sql / views.sql).
INSERT INTO Repair_Knowledge (
    OBD_Code, Repair_Priority, Estimated_Repair_Cost_Min_INR,
    Estimated_Repair_Cost_Max_INR, Estimated_Labor_Hours_Min, Estimated_Labor_Hours_Max
)
SELECT
    OBD_Code, Repair_Priority, Estimated_Repair_Cost_Min_INR,
    Estimated_Repair_Cost_Max_INR, Estimated_Labor_Hours_Min, Estimated_Labor_Hours_Max
FROM staging_repair_knowledge;

-- Cleanup — staging tables have done their job, remove them so they
-- don't clutter the schema or risk being queried as if they were live data.
DROP TABLE staging_vehicle_master;
DROP TABLE staging_obd_codes;
DROP TABLE staging_vehicle_maintenance;
DROP TABLE staging_repair_knowledge;
