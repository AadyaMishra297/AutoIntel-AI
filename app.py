"""
app.py — AutoIntel AI Streamlit Application (Member 4)

Run with:  streamlit run app.py
"""

import streamlit as st
from src import db
from src.complaint_adapter import analyze_complaint

st.set_page_config(page_title="AutoIntel AI", page_icon="🚗", layout="centered")

st.title("🚗 AutoIntel AI — Vehicle Diagnosis Assistant")
st.caption("Select a vehicle, describe the issue, and get an instant diagnosis report.")

# ---------------------------------------------------------------
# 1. Vehicle Selection
# ---------------------------------------------------------------
st.header("1. Select Vehicle")

vehicles = db.get_all_vehicles()

if not vehicles:
    st.error("No vehicles found in the database. Please check database/autointel.db.")
    st.stop()

def vehicle_label(v):
    variant = f" {v['Variant']}" if v.get("Variant") else ""
    return f"{v['Brand']} {v['Model']}{variant} ({v['Manufacturing_Year']}) — ID {v['Vehicle_ID']}"

vehicle_labels = {vehicle_label(v): v["Vehicle_ID"] for v in vehicles}
selected_label = st.selectbox("Vehicle", list(vehicle_labels.keys()))
selected_vehicle_id = vehicle_labels[selected_label]
vehicle = db.get_vehicle_by_id(selected_vehicle_id)

with st.expander("Vehicle details", expanded=False):
    st.write(f"**Brand/Model:** {vehicle['Brand']} {vehicle['Model']} {vehicle.get('Variant') or ''}")
    st.write(f"**Year:** {vehicle['Manufacturing_Year']}")
    st.write(f"**Engine:** {vehicle.get('Engine') or vehicle.get('engine_size') or 'N/A'}")
    st.write(f"**Fuel Type:** {vehicle.get('fuel_type') or 'N/A'}")

# ---------------------------------------------------------------
# 2. Complaint Entry
# ---------------------------------------------------------------
st.header("2. Describe the Complaint")

complaint_text = st.text_area(
    "What issue is the vehicle experiencing?",
    placeholder="e.g. Car shakes and engine feels rough at idle...",
    height=100,
)

analyze_clicked = st.button("Analyze & Generate Diagnosis Report", type="primary")

# ---------------------------------------------------------------
# 3. Diagnosis Report
# ---------------------------------------------------------------
if analyze_clicked:
    if not complaint_text.strip():
        st.warning("Please enter a complaint description first.")
        st.stop()

    result = analyze_complaint(complaint_text)
    obd = result["obd_code"]

    db.save_complaint(
        vehicle_id=selected_vehicle_id,
        complaint_text=complaint_text,
        matched_obd_code=obd["OBD_Code"] if obd else None,
    )

    st.header("3. Diagnosis Report")

    if obd is None:
        st.warning(
            "No matching OBD fault found for this complaint. "
            "Consider manual inspection or adding more detail."
        )
    else:
        repair = db.get_repair_for_obd(obd["OBD_Code"])
        maintenance = db.get_maintenance_for_vehicle(selected_vehicle_id)
        latest = maintenance[0] if maintenance else None

        st.success(f"Match confidence: {result['confidence'] * 100:.0f}%")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Vehicle")
            st.write(f"{vehicle['Brand']} {vehicle['Model']} ({vehicle['Manufacturing_Year']})")
            if latest:
                st.write(f"Mileage: {latest.get('mileage', 'N/A')} km")
        with col2:
            st.subheader("Detected Fault")
            st.write(f"OBD Code: `{obd['OBD_Code']}`")
            st.write(obd.get("Description") or "")
            if obd.get("Fault_Description"):
                st.caption(obd["Fault_Description"])
            if obd.get("Severity_Level") or obd.get("Severity"):
                st.write(f"Severity: {obd.get('Severity_Level') or obd.get('Severity')}")

        st.divider()
        st.subheader("Repair Solution")
        st.write(obd.get("Work_Required") or "No specific repair guidance on file for this code.")
        if repair:
            rcol1, rcol2 = st.columns(2)
            cost_min = repair.get("Estimated_Repair_Cost_Min_INR")
            cost_max = repair.get("Estimated_Repair_Cost_Max_INR")
            hours_min = repair.get("Estimated_Labor_Hours_Min")
            hours_max = repair.get("Estimated_Labor_Hours_Max")
            rcol1.metric("Estimated Cost", f"₹{cost_min:.0f}–₹{cost_max:.0f}" if cost_min is not None else "N/A")
            rcol2.metric("Estimated Time", f"{hours_min}–{hours_max} hrs" if hours_min is not None else "N/A")
            if repair.get("Repair_Priority"):
                st.caption(f"Priority: {repair['Repair_Priority']}")
        else:
            st.caption("No cost/time estimate on file for this OBD code.")

        st.divider()
        st.subheader("Preventive Maintenance")
        if latest:
            tips = []
            if latest.get("Maintenance_Risk_Level"):
                tips.append(f"Current maintenance risk level: **{latest['Maintenance_Risk_Level']}**")
            if latest.get("Service_Due_Status"):
                tips.append(f"Service due status: **{latest['Service_Due_Status']}**")
            if latest.get("Component_Wear_Score") is not None:
                tips.append(f"Component wear score: **{latest['Component_Wear_Score']}**")
            if latest.get("Vehicle_Health_Score") is not None:
                tips.append(f"Overall vehicle health score: **{latest['Vehicle_Health_Score']}**")
            if tips:
                for t in tips:
                    st.write(f"- {t}")
            else:
                st.write("No risk/health indicators on file for this vehicle.")
        else:
            st.write("No maintenance record on file to base a preventive tip on.")

        st.divider()
        st.subheader("Maintenance History")
        if maintenance:
            for m in maintenance:
                st.write(
                    f"- **{m.get('last_service_date', 'Unknown date')}** — "
                    f"{m.get('maintenance_history') or 'No details'} "
                    f"(reported issues: {m.get('reported_issues') or 'none'})"
                )
        else:
            st.write("No maintenance history on file for this vehicle.")

        st.caption(f"Matched keywords: {', '.join(result['matched_keywords']) or 'none'}")

st.divider()
st.caption("AutoIntel AI — Member 4 prototype, wired to the real autointel.db schema.")
