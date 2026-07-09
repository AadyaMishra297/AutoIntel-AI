"""
test_end_to_end.py — End-to-end testing for Member 4's integration,
against the REAL autointel.db schema.

Run with: python -m tests.test_end_to_end   (from project root)
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import db
from src.complaint_adapter import analyze_complaint


def test_db_connection():
    vehicles = db.get_all_vehicles()
    assert len(vehicles) > 0, "No vehicles found — check database/autointel.db is the real file"
    print(f"[PASS] DB connection OK — {len(vehicles)} vehicles found")


def test_vehicle_lookup():
    vehicles = db.get_all_vehicles()
    v = db.get_vehicle_by_id(vehicles[0]["Vehicle_ID"])
    assert v is not None
    print(f"[PASS] Vehicle lookup OK — {v['Brand']} {v['Model']}")


def test_obd_codes_loaded():
    codes = db.get_all_obd_codes()
    assert len(codes) > 0, "No OBD codes found"
    print(f"[PASS] OBD_Codes loaded — {len(codes)} codes found")


def test_complaint_analysis_matches():
    result = analyze_complaint("Engine shaking and rough idle")
    assert result["obd_code"] is not None, "Expected an OBD code match"
    print(f"[PASS] Complaint analysis matched: {result['obd_code']['OBD_Code']} "
          f"({result['confidence']*100:.0f}% confidence)")


def test_repair_lookup():
    vehicles = db.get_all_vehicles()
    result = analyze_complaint("Engine shaking and rough idle")
    if result["obd_code"]:
        repair = db.get_repair_for_obd(result["obd_code"]["OBD_Code"])
        print(f"[PASS] Repair lookup OK — {repair}")
    else:
        print("[SKIP] No OBD match to look up repair for")


def test_maintenance_history():
    vehicles = db.get_all_vehicles()
    history = db.get_maintenance_for_vehicle(vehicles[0]["Vehicle_ID"])
    print(f"[PASS] Maintenance history lookup OK — {len(history)} record(s) found")


def test_complaint_saved():
    vehicles = db.get_all_vehicles()
    vehicle_id = vehicles[0]["Vehicle_ID"]
    result = analyze_complaint("battery seems dead, car won't start")
    complaint_id = db.save_complaint(
        vehicle_id, "battery seems dead, car won't start",
        result["obd_code"]["OBD_Code"] if result["obd_code"] else None
    )
    assert complaint_id is not None
    print(f"[PASS] Complaint saved with ID {complaint_id}")


if __name__ == "__main__":
    tests = [
        test_db_connection,
        test_vehicle_lookup,
        test_obd_codes_loaded,
        test_complaint_analysis_matches,
        test_repair_lookup,
        test_maintenance_history,
        test_complaint_saved,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            failed += 1
            print(f"[FAIL] {t.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"[ERROR] {t.__name__}: {type(e).__name__}: {e}")
    print()
    if failed:
        print(f"{failed} test(s) FAILED")
        sys.exit(1)
    else:
        print("All tests PASSED ✅")
