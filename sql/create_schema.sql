

CREATE TABLE Vehicle_Master (
    Vehicle_ID          TEXT PRIMARY KEY,
    vehicle_model        TEXT,
    Brand                 TEXT,
    Model                 TEXT,
    Variant               TEXT,
    fuel_type             TEXT,
    engine_size           INTEGER,
    Engine                TEXT,
    Manufacturing_Year    INTEGER
);

CREATE TABLE OBD_Codes (
    OBD_Code            TEXT PRIMARY KEY,
    Description          TEXT,
    Category              TEXT,
    Severity              TEXT,
    Fault_Description     TEXT,
    Work_Required          TEXT,
    Severity_Level         INTEGER,
    Primary_System          TEXT
);

CREATE TABLE Vehicle_Maintenance (
    Maintenance_ID              INTEGER PRIMARY KEY AUTOINCREMENT,
    Vehicle_ID                   TEXT NOT NULL,
    vehicle_model                 TEXT,
    mileage                       INTEGER,
    maintenance_history           TEXT,
    reported_issues                INTEGER,
    vehicle_age                    INTEGER,
    fuel_type                      TEXT,
    transmission_type               TEXT,
    engine_size                     INTEGER,
    odometer_reading                 INTEGER,
    last_service_date                 TEXT,
    warranty_expiry_date               TEXT,
    owner_type                          TEXT,
    insurance_premium                    INTEGER,
    service_history                       INTEGER,
    accident_history                       INTEGER,
    fuel_efficiency                         REAL,
    tire_condition                           TEXT,
    brake_condition                           TEXT,
    battery_status                             TEXT,
    need_maintenance                            INTEGER,
    Months_Since_Last_Service                    REAL,
    Warranty_Status                               TEXT,
    Warranty_Remaining_Months                      REAL,
    Odometer_Category                               TEXT,
    Fuel_Efficiency_Rating                           TEXT,
    Annual_Mileage                                    REAL,
    Vehicle_Usage_Category                             TEXT,
    Service_Due_Status                                  TEXT,
    Component_Wear_Score                                 REAL,
    Issue_Rate                                            REAL,
    Vehicle_Health_Score                                   REAL,
    Maintenance_Risk_Level                                  TEXT,
    FOREIGN KEY (Vehicle_ID) REFERENCES Vehicle_Master(Vehicle_ID)
);

-- Note: Description, Category, Severity, Severity_Level, Primary_System,
-- and Work_Required are deliberately NOT included here — they already
-- live in OBD_Codes and are retrieved via JOIN, not duplicated.
CREATE TABLE Repair_Knowledge (
    OBD_Code                          TEXT PRIMARY KEY,
    Repair_Priority                    TEXT,
    Estimated_Repair_Cost_Min_INR       REAL,
    Estimated_Repair_Cost_Max_INR        REAL,
    Estimated_Labor_Hours_Min             REAL,
    Estimated_Labor_Hours_Max              REAL,
    FOREIGN KEY (OBD_Code) REFERENCES OBD_Codes(OBD_Code)
);
