import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "autointel.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    _ensure_complaints_table(conn)
    return conn


def _ensure_complaints_table(conn):
    conn.execute(
        """CREATE TABLE IF NOT EXISTS Complaints (
            Complaint_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Vehicle_ID INTEGER,
            Complaint_Text TEXT,
            Matched_OBD_Code TEXT,
            Created_At TEXT DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    conn.commit()


# ---------------------------------------------------------------
# Vehicles
# ---------------------------------------------------------------

def get_all_vehicles():
    conn = get_connection()
    rows = conn.execute(
        """SELECT Vehicle_ID, Brand, Model, Variant, vehicle_model,
                  fuel_type, engine_size, Engine, Manufacturing_Year
           FROM Vehicle_Master
           ORDER BY Brand, Model"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_vehicle_by_id(vehicle_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM Vehicle_Master WHERE Vehicle_ID = ?", (vehicle_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------------------------------------------------------
# OBD Codes / Faults
# ---------------------------------------------------------------

def get_all_obd_codes():
    conn = get_connection()
    rows = conn.execute(
        """SELECT OBD_Code, Description, Category, Severity,
                  Fault_Description, Work_Required, Severity_Level,
                  Primary_System
           FROM OBD_Codes"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_obd_code(obd_code):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM OBD_Codes WHERE OBD_Code = ?", (obd_code,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------------------------------------------------------
# Repair estimates
# ---------------------------------------------------------------

def get_repair_for_obd(obd_code):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM Repair_Knowledge WHERE OBD_Code = ?", (obd_code,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------------------------------------------------------
# Maintenance history
# ---------------------------------------------------------------

def get_maintenance_for_vehicle(vehicle_id):
    """Returns all Vehicle_Maintenance rows for this vehicle, most recent first."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM Vehicle_Maintenance
           WHERE Vehicle_ID = ?
           ORDER BY last_service_date DESC""",
        (vehicle_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_latest_maintenance_for_vehicle(vehicle_id):
    history = get_maintenance_for_vehicle(vehicle_id)
    return history[0] if history else None


# ---------------------------------------------------------------
# Complaints (logged locally — no source table for this exists)
# ---------------------------------------------------------------

def save_complaint(vehicle_id, complaint_text, matched_obd_code):
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO Complaints (Vehicle_ID, Complaint_Text, Matched_OBD_Code)
           VALUES (?, ?, ?)""",
        (vehicle_id, complaint_text, matched_obd_code),
    )
    conn.commit()
    complaint_id = cur.lastrowid
    conn.close()
    return complaint_id
