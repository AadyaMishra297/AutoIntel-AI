"""
app.py — AutoIntel AI Streamlit Application (Member 4)

Run with:  streamlit run app.py

Backend logic (src/db.py, src/complaint_adapter.py, the TF-IDF matching
engine, and the SQLite schema) is unchanged. This file only adds a
professional presentation layer on top of the same calls and results
the original app used: db.get_all_vehicles(), db.get_vehicle_by_id(),
analyze_complaint(), db.save_complaint(), db.get_repair_for_obd(),
db.get_maintenance_for_vehicle().
"""

from datetime import datetime

import streamlit as st
from src import db
from src.complaint_adapter import analyze_complaint
from src.report_generator import build_pdf_report
from src.ui_helpers import (
    load_css,
    similarity_status,
    health_status,
    risk_color,
    status_badge,
    section_header,
)

st.set_page_config(page_title="AutoIntel AI", page_icon=":material/directions_car:", layout="wide")
load_css()

st.markdown(
    '<div style="text-align:center; margin-bottom:0.5rem;">'
    '<h1 style="margin-bottom:0.3rem;">AutoIntel AI</h1>'
    '<p style="color:var(--text-color); opacity:0.65; font-size:0.95rem; margin:0;">'
    "Vehicle Diagnosis Assistant &mdash; select a vehicle, describe the issue, "
    "and generate a diagnosis report."
    "</p>"
    "</div>",
    unsafe_allow_html=True,
)
st.divider()

# ---------------------------------------------------------------
# 1. Select Vehicle
# ---------------------------------------------------------------
section_header("1. Select Vehicle")

vehicles = db.get_all_vehicles()

if not vehicles:
    st.error("No vehicles found in the database. Please check database/autointel.db.")
    st.stop()


def vehicle_label(v):
    variant = f" {v['Variant']}" if v.get("Variant") else ""
    return f"{v['Brand']} {v['Model']}{variant} ({v['Manufacturing_Year']}) — ID {v['Vehicle_ID']}"


vehicle_labels = {vehicle_label(v): v["Vehicle_ID"] for v in vehicles}

col_select, col_spacer = st.columns([2, 1])
with col_select:
    selected_label = st.selectbox("Vehicle", list(vehicle_labels.keys()))

selected_vehicle_id = vehicle_labels[selected_label]
vehicle = db.get_vehicle_by_id(selected_vehicle_id)

vehicle_detail_lines = [
    f"Brand/Model: {vehicle['Brand']} {vehicle['Model']} {vehicle.get('Variant') or ''}".strip(),
    f"Year: {vehicle['Manufacturing_Year']}",
    f"Engine: {vehicle.get('Engine') or vehicle.get('engine_size') or 'N/A'}",
    f"Fuel Type: {vehicle.get('fuel_type') or 'N/A'}",
]

with st.expander("Vehicle Details", expanded=False):
    for line in vehicle_detail_lines:
        label_part, value_part = line.split(":", 1)
        st.write(f"**{label_part}:**{value_part}")

st.divider()

# ---------------------------------------------------------------
# 2. Describe the Complaint
# ---------------------------------------------------------------
section_header("2. Describe the Complaint")

complaint_text = st.text_area(
    "What issue is the vehicle experiencing?",
    placeholder="e.g. Car shakes and engine feels rough at idle...",
    height=100,
    label_visibility="collapsed",
)

analyze_clicked = st.button("Analyze & Generate Diagnosis Report", type="primary")

if analyze_clicked and not complaint_text.strip():
    st.warning("Please enter a complaint description first.")

# ---------------------------------------------------------------
# Run analysis (unchanged backend calls) and cache result in session
# ---------------------------------------------------------------
if analyze_clicked and complaint_text.strip():
    result = analyze_complaint(complaint_text)
    obd = result["obd_code"]

    db.save_complaint(
        vehicle_id=selected_vehicle_id,
        complaint_text=complaint_text,
        matched_obd_code=obd["OBD_Code"] if obd else None,
    )

    st.session_state["autointel_diagnosis"] = {
        "vehicle": vehicle,
        "vehicle_label": selected_label,
        "vehicle_detail_lines": vehicle_detail_lines,
        "complaint_text": complaint_text,
        "result": result,
        "obd": obd,
        "repair": db.get_repair_for_obd(obd["OBD_Code"]) if obd else None,
        "maintenance": db.get_maintenance_for_vehicle(selected_vehicle_id),
    }

# ---------------------------------------------------------------
# 3. Diagnosis Report
# ---------------------------------------------------------------
diagnosis = st.session_state.get("autointel_diagnosis")

if diagnosis:
    st.divider()
    section_header("3. Diagnosis Report")

    result = diagnosis["result"]
    obd = diagnosis["obd"]
    repair = diagnosis["repair"]
    maintenance = diagnosis["maintenance"]
    latest = maintenance[0] if maintenance else None

    if obd is None:
        st.warning(
            "No matching OBD fault found for this complaint. "
            "Consider manual inspection or adding more detail."
        )
    else:
        score_pct = result["confidence"] * 100
        sim_label, sim_color = similarity_status(score_pct)

        health_score = latest.get("Vehicle_Health_Score") if latest else None
        health_label, health_color = health_status(health_score)
        maint_risk = latest.get("Maintenance_Risk_Level") if latest else None

        cost_min = repair.get("Estimated_Repair_Cost_Min_INR") if repair else None
        cost_max = repair.get("Estimated_Repair_Cost_Max_INR") if repair else None
        hours_min = repair.get("Estimated_Labor_Hours_Min") if repair else None
        hours_max = repair.get("Estimated_Labor_Hours_Max") if repair else None
        cost_display = f"Rs.{cost_min:.0f}-{cost_max:.0f}" if cost_min is not None else "N/A"
        time_display = f"{hours_min}-{hours_max} hrs" if hours_min is not None else "N/A"

        # ---- Top metric row -------------------------------------------------
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Similarity Score", f"{score_pct:.0f}%")
        m2.metric("Vehicle Health", f"{health_score:.0f}" if health_score is not None else "N/A")
        m3.metric("Estimated Cost", cost_display)
        m4.metric("Repair Time", time_display)

        # ---- Similarity Score dashboard --------------------------------------
        with st.container(border=True):
            section_header("Similarity Score")
            st.progress(min(max(score_pct / 100, 0.0), 1.0))
            st.markdown(
                f"**{score_pct:.0f}%** &nbsp; {status_badge(sim_label, sim_color)}",
                unsafe_allow_html=True,
            )

        # ---- Vehicle & Fault (two-column) -------------------------------------
        col_vehicle, col_fault = st.columns(2)
        with col_vehicle:
            with st.container(border=True):
                section_header("Vehicle")
                st.write(f"{vehicle['Brand']} {vehicle['Model']} ({vehicle['Manufacturing_Year']})")
                if latest:
                    st.write(f"Mileage: {latest.get('mileage', 'N/A')} km")
        with col_fault:
            with st.container(border=True):
                section_header("Detected Fault")
                st.write(f"OBD Code: `{obd['OBD_Code']}`")
                st.write(obd.get("Description") or "")
                if obd.get("Fault_Description"):
                    st.caption(obd["Fault_Description"])
                if obd.get("Severity_Level") or obd.get("Severity"):
                    st.write(f"Severity: {obd.get('Severity_Level') or obd.get('Severity')}")

        # ---- Repair Solution -----------------------------------------------
        with st.container(border=True):
            section_header("Repair Solution")
            repair_solution_text = obd.get("Work_Required") or "No specific repair guidance on file for this code."
            st.write(repair_solution_text)
            rcol1, rcol2 = st.columns(2)
            rcol1.metric("Estimated Cost", cost_display)
            rcol2.metric("Estimated Time", time_display)
            if repair and repair.get("Repair_Priority"):
                st.caption(f"Priority: {repair['Repair_Priority']}")
            elif not repair:
                st.caption("No cost/time estimate on file for this OBD code.")

        # ---- Vehicle Health Dashboard ----------------------------------------
        with st.container(border=True):
            section_header("Vehicle Health Dashboard")
            if latest and health_score is not None:
                hcol1, hcol2 = st.columns([2, 1])
                with hcol1:
                    st.progress(min(max(health_score / 100, 0.0), 1.0))
                    st.markdown(
                        f"**{health_score:.0f} / 100** &nbsp; {status_badge(health_label, health_color)}",
                        unsafe_allow_html=True,
                    )
                with hcol2:
                    st.markdown(
                        f"Maintenance Risk<br/>{status_badge(maint_risk or 'N/A', risk_color(maint_risk))}",
                        unsafe_allow_html=True,
                    )
            else:
                st.write("No vehicle health data on file for this vehicle.")

        # ---- Preventive Maintenance & Maintenance History (expanders) --------
        with st.expander("Preventive Maintenance", expanded=False):
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

        with st.expander("Maintenance History", expanded=False):
            if maintenance:
                for m in maintenance:
                    st.write(
                        f"- **{m.get('last_service_date', 'Unknown date')}** — "
                        f"{m.get('maintenance_history') or 'No details'} "
                        f"(reported issues: {m.get('reported_issues') or 'none'})"
                    )
            else:
                st.write("No maintenance history on file for this vehicle.")

        # ---- AI Explanation ---------------------------------------------------
        matched_keywords = result["matched_keywords"]
        explanation_lines = [
            f"User complaint: \"{diagnosis['complaint_text']}\"",
            (
                f"Keywords extracted: {', '.join(matched_keywords)}"
                if matched_keywords
                else "Keywords extracted: none identified"
            ),
            (
                "The complaint was compared against historical complaint records in the "
                "database using a text-similarity engine, which scored this entry as a "
                f"{score_pct:.0f}% match ({sim_label.lower()})."
            ),
            (
                f"OBD fault {obd['OBD_Code']}"
                + (f" ({obd.get('Description')})" if obd.get("Description") else "")
                + " was selected because it corresponds to the historical complaint record "
                "with the highest similarity score to this description"
                + (f", within the {obd.get('Primary_System')} system" if obd.get("Primary_System") else "")
                + "."
            ),
        ]

        with st.container(border=True):
            section_header("AI Explanation", "How this diagnosis was reached")
            for line in explanation_lines:
                st.write(f"- {line}")

        # ---- Download report ---------------------------------------------------
        preventive_lines = (
            [
                f"Current maintenance risk level: {latest.get('Maintenance_Risk_Level')}",
                f"Service due status: {latest.get('Service_Due_Status')}",
                f"Component wear score: {latest.get('Component_Wear_Score')}",
                f"Overall vehicle health score: {latest.get('Vehicle_Health_Score')}",
            ]
            if latest
            else []
        )

        pdf_data = {
            "vehicle_label": diagnosis["vehicle_label"],
            "vehicle_details": diagnosis["vehicle_detail_lines"],
            "complaint_text": diagnosis["complaint_text"],
            "similarity_score_pct": score_pct,
            "similarity_status": sim_label,
            "obd_code": obd.get("OBD_Code"),
            "obd_description": obd.get("Description"),
            "fault_description": obd.get("Fault_Description"),
            "severity": obd.get("Severity_Level") or obd.get("Severity"),
            "repair_solution": repair_solution_text,
            "estimated_cost": cost_display,
            "estimated_time": time_display,
            "vehicle_health_score": f"{health_score:.0f}" if health_score is not None else "N/A",
            "health_status": health_label,
            "maintenance_risk": maint_risk or "N/A",
            "maintenance_history": [
                f"{m.get('last_service_date', 'Unknown date')} — "
                f"{m.get('maintenance_history') or 'No details'} "
                f"(reported issues: {m.get('reported_issues') or 'none'})"
                for m in maintenance
            ],
            "preventive_maintenance": preventive_lines,
            "ai_explanation": explanation_lines,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        pdf_bytes = build_pdf_report(pdf_data)
        st.download_button(
            label="Download Diagnosis Report (PDF)",
            data=pdf_bytes,
            file_name=f"AutoIntel_Diagnosis_{obd.get('OBD_Code', 'report')}.pdf",
            mime="application/pdf",
        )

st.divider()
st.caption("AutoIntel AI — vehicle diagnosis dashboard, wired to the autointel.db schema.")
