"""
AutoIntel AI - Week 1 Dataset Generation Pipeline
Member 2 (OBD-II Knowledge Engineer) + Member 3 (Database & Knowledge Base Engineer)

Produces:
  1. obd_knowledge.csv        - cleaned & standardized full OBD-II P-code reference
                                 (Category, Severity, Fault_Description, Work_Required added)
  2. repair_knowledge.csv     - curated, high-quality fault -> repair mapping (~50 records)
                                 with Indian market cost/time estimates

Input:
  obd_codes_clean.csv  (columns: OBD_Code, Description, Description_Length, Prefix)

Usage:
  python generate_datasets.py --input obd_codes_clean.csv --outdir out
"""

import argparse
import csv
import re
import os

# ---------------------------------------------------------------------------
# PART 1: OBD-II dataset cleaning & standardization  ->  obd_knowledge.csv
# ---------------------------------------------------------------------------

CODE_PATTERN = re.compile(r"^[PBCU]\d[0-9A-F]{3}$")

# Standard SAE J2012 P-code range categories (numeric portion of the code)
def categorize(code: str) -> str:
    prefix = code[0:2]          # e.g. "P0", "P1", "P2", "P3"
    num_part = code[2:]         # e.g. "217", "00A"
    try:
        num = int(num_part)      # plain decimal for normal codes like "217"
    except ValueError:
        try:
            num = int(num_part, 16)  # hex-suffixed codes like "00A" -> P000A
        except ValueError:
            num = 0

    if prefix == "P0":
        if 0 <= num <= 99:
            return "Fuel and Air Metering"
        if 100 <= num <= 199:
            return "Fuel and Air Metering"
        if 200 <= num <= 299:
            return "Fuel and Air Metering (Injector Circuit)"
        if 300 <= num <= 399:
            return "Ignition System / Misfire"
        if 400 <= num <= 499:
            return "Auxiliary Emission Controls"
        if 500 <= num <= 599:
            return "Vehicle Speed & Idle Control System"
        if 600 <= num <= 699:
            return "Computer Output Circuit"
        if 700 <= num <= 899:
            return "Transmission"
        return "Fuel and Air Metering"

    if prefix == "P1":
        return "Manufacturer-Specific"

    if prefix == "P2":
        if 0 <= num <= 99:
            return "Fuel and Air Metering"
        if 100 <= num <= 199:
            return "Fuel and Air Metering (Throttle/Pedal)"
        if 200 <= num <= 299:
            return "Fuel and Air Metering (O2 Sensor)"
        if 300 <= num <= 399:
            return "Ignition System / Misfire"
        if 400 <= num <= 499:
            return "Auxiliary Emission Controls"
        if 500 <= num <= 599:
            return "Computer Output Circuit / Charging System"
        if 600 <= num <= 799:
            return "Computer Output Circuit"
        if 800 <= num <= 999:
            return "Transmission"
        return "Manufacturer-Specific"

    if prefix == "P3":
        if 400 <= num <= 999:
            return "Ignition System / Misfire (Cylinder Deactivation)"
        return "Manufacturer-Specific"

    return "Manufacturer-Specific"


# Keyword-based severity heuristic
SEVERITY_HIGH_KEYWORDS = [
    "misfire", "overheat", "over temperature", "overspeed", "stuck on",
    "stuck off", "stuck open", "stuck closed", "no start", "over pressure",
    "voltage low", "voltage high",
]
SEVERITY_LOW_KEYWORDS = [
    "small leak", "vent", "evap", "heater resistance", "ambient",
]

def assign_severity(description: str) -> str:
    d = description.lower()
    if any(k in d for k in SEVERITY_HIGH_KEYWORDS):
        return "High"
    if any(k in d for k in SEVERITY_LOW_KEYWORDS):
        return "Low"
    return "Medium"


WORK_REQUIRED_BY_CATEGORY = {
    "Fuel and Air Metering":
        "Inspect fuel delivery, air metering sensors (MAF/MAP), and related wiring; "
        "test with a scan tool and repair or replace the faulty sensor, injector, or circuit.",
    "Fuel and Air Metering (Injector Circuit)":
        "Test injector circuit resistance and driver signal; inspect wiring/connector "
        "and replace the injector or repair the circuit as needed.",
    "Fuel and Air Metering (Throttle/Pedal)":
        "Inspect throttle body, pedal position sensor, and related wiring; clean carbon "
        "deposits and recalibrate or replace the sensor if faulty.",
    "Fuel and Air Metering (O2 Sensor)":
        "Inspect oxygen sensor wiring and exhaust for leaks; test sensor response and "
        "replace the sensor if it fails to switch correctly.",
    "Ignition System / Misfire":
        "Inspect spark plugs, ignition coils, and crank/cam position sensors; isolate the "
        "affected cylinder and repair the ignition or mechanical fault causing the misfire.",
    "Ignition System / Misfire (Cylinder Deactivation)":
        "Inspect the cylinder deactivation/valve control solenoid and wiring for the "
        "affected cylinder; test actuator operation and replace faulty components.",
    "Auxiliary Emission Controls":
        "Inspect EGR, EVAP, and catalytic converter systems for leaks, clogging, or "
        "actuator faults; clean or replace the affected component.",
    "Vehicle Speed & Idle Control System":
        "Inspect throttle body, idle air control valve, and vehicle speed sensor "
        "circuits; clean or replace faulty components and verify idle stability.",
    "Computer Output Circuit":
        "Inspect ECM/PCM wiring, relays, and output driver circuits; test control "
        "module operation and reprogram or replace if an internal fault is confirmed.",
    "Computer Output Circuit / Charging System":
        "Inspect charging system wiring and control circuits; test alternator/voltage "
        "regulator output and repair or replace faulty components.",
    "Transmission":
        "Inspect transmission solenoids, speed sensors, and fluid condition; diagnose "
        "the internal transmission fault indicated and repair or replace as required.",
    "Manufacturer-Specific":
        "Consult manufacturer service documentation for this proprietary code; inspect "
        "the specific system or component referenced in the fault description.",
}


def clean_obd_dataset(input_path: str, output_path: str) -> int:
    """Clean, deduplicate, standardize and enrich the OBD-II code dataset."""
    rows = []
    seen_codes = set()

    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row["OBD_Code"].strip().upper()
            desc = row["Description"].strip()

            # Drop malformed rows where Description is itself an OBD code
            # (data-entry/row-shift errors in the source file)
            if CODE_PATTERN.match(desc):
                continue

            # Drop rows with missing/empty description
            if not desc:
                continue

            # Deduplicate on OBD_Code, keep first valid occurrence
            if code in seen_codes:
                continue
            seen_codes.add(code)

            category = categorize(code)
            severity = assign_severity(desc)
            work_required = WORK_REQUIRED_BY_CATEGORY[category]

            rows.append({
                "OBD_Code": code,
                "Description": desc,
                "Category": category,
                "Severity": severity,
                "Fault_Description": desc,
                "Work_Required": work_required,
            })

    fieldnames = ["OBD_Code", "Description", "Category", "Severity",
                  "Fault_Description", "Work_Required"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


# ---------------------------------------------------------------------------
# PART 2: Curated repair knowledge dataset  ->  repair_knowledge.csv
# ---------------------------------------------------------------------------

REPAIR_ROWS = [
["P0011","A Camshaft Position - Timing Over-Advanced or System Performance Bank 1",
 "Worn timing chain/tensioner, low or degraded engine oil affecting VVT oil control valve, or a stuck/failed camshaft phaser/actuator on Bank 1",
 "Inspect timing chain and tensioner for wear; replace VVT solenoid/oil control valve if clogged with sludge; change engine oil and filter with correct viscosity oil; clear codes and verify camshaft timing with a scan tool",
 "3500-9000","2-4 hours","Medium",
 "Use manufacturer-recommended engine oil and change it every 5,000-7,500 km; avoid extended oil-change intervals which cause VVT solenoid sludging"],
["P0016","Crankshaft Position - Camshaft Position Correlation Bank 1 Sensor A",
 "Timing chain stretch or jumped tooth, worn timing chain guides, or a failing crankshaft/camshaft position sensor causing signal misalignment",
 "Verify timing marks/chain alignment, replace stretched timing chain and guides if worn, replace faulty crank or cam sensor, then clear codes and re-verify sync at idle and under load",
 "6000-18000","3-6 hours","High",
 "Replace timing chain kit at manufacturer-specified intervals (typically 90,000-120,000 km) and use quality engine oil to reduce chain wear"],
["P0087","Fuel Rail/System Pressure - Too Low Bank 1",
 "Weak or failing fuel pump, clogged fuel filter, leaking fuel pressure regulator, or a restricted/leaking high-pressure fuel line",
 "Test fuel pump output pressure and volume, replace fuel filter, inspect and replace fuel pressure regulator or high-pressure pump if pressure remains low, then check for line leaks",
 "4500-14000","2-5 hours","High",
 "Replace fuel filter every 20,000-30,000 km and always use fuel from reputable stations to avoid contamination and premature pump wear"],
["P0088","Fuel Rail/System Pressure - Too High Bank 1",
 "Stuck-closed fuel pressure regulator, blocked fuel return line, or a faulty high-pressure fuel pump control causing excess rail pressure",
 "Inspect and replace the fuel pressure regulator, clear any blockage in the return line, and reprogram/replace the fuel pump control module if pressure stays out of spec",
 "5000-15000","2-5 hours","High",
 "Have fuel system pressure checked during periodic services; avoid aftermarket fuel pump modules of unverified quality"],
["P0102","Mass or Volume Air Flow Sensor A Circuit Low",
 "Dirty or contaminated MAF sensor element, damaged wiring/connector, or air intake leak upstream of the sensor causing a low signal",
 "Clean the MAF sensor with dedicated MAF cleaner, inspect intake ducting and connector for leaks or damage, repair wiring, and replace the sensor if cleaning does not restore correct readings",
 "1500-6000","1-2 hours","Medium",
 "Clean or replace the air filter every 10,000-15,000 km and avoid oiled aftermarket filters that can contaminate the MAF sensor"],
["P0103","Mass or Volume Air Flow Sensor A Circuit High",
 "MAF sensor circuit short to voltage, damaged sensor element, or a poor ground connection sending an abnormally high signal",
 "Inspect wiring harness for shorts or chafing, check sensor ground connection, and replace the MAF sensor if it fails bench/scan tool testing",
 "1500-6000","1-2 hours","Medium",
 "Periodically inspect the engine wiring harness near the intake for chafing and secure loose looms"],
["P0106","Manifold Absolute Pressure/Barometric Pressure Sensor Circuit Range/Performance",
 "Vacuum leak near the intake manifold, clogged or dirty MAP sensor port, or a failing MAP sensor giving an out-of-range reading",
 "Inspect intake manifold and vacuum hoses for leaks and cracks, clean the MAP sensor port, and replace the MAP sensor if readings remain outside expected range",
 "1200-4500","1-2 hours","Medium",
 "Inspect vacuum hoses for cracking or hardening every 20,000 km, especially in hot climates"],
["P0113","Intake Air Temperature Sensor 1 Circuit High Bank 1",
 "Open circuit or damaged wiring in the IAT sensor circuit, corroded connector, or a failed sensor reading unrealistically high resistance",
 "Inspect and repair wiring/connector for open circuit or corrosion, and replace the IAT sensor if the fault persists after wiring repair",
 "800-3000","1 hour","Low",
 "Keep engine bay wiring connectors clean and protected from moisture during monsoon season"],
["P0117","Engine Coolant Temperature Sensor 1 Circuit Low",
 "Short to ground in ECT sensor wiring, corroded connector, or a failed coolant temperature sensor reading abnormally low resistance",
 "Inspect and repair the wiring for shorts, clean/replace the connector, and replace the ECT sensor if it fails resistance testing",
 "700-2500","1 hour","Medium",
 "Check coolant condition and top-up level at every service; replace coolant per manufacturer schedule to prevent sensor corrosion"],
["P0121","Throttle/Pedal Position Sensor/Switch A Circuit Range/Performance",
 "Worn or dirty throttle position sensor, loose sensor mounting, or throttle body carbon buildup affecting sensor linearity",
 "Clean the throttle body and sensor area, recalibrate/relearn throttle position after cleaning, and replace the TPS if voltage output remains erratic",
 "1500-5000","1-2 hours","Medium",
 "Clean the throttle body every 20,000-25,000 km to prevent carbon buildup affecting sensor accuracy"],
["P0128","Coolant Thermostat (Coolant Temperature Below Thermostat Regulating Temperature)",
 "Thermostat stuck open, allowing coolant to circulate before the engine reaches operating temperature, often due to age or a weak spring",
 "Replace the thermostat and gasket/O-ring, flush and refill coolant to correct level, and verify the engine reaches normal operating temperature",
 "1200-4000","1-2 hours","Medium",
 "Replace the thermostat every 60,000-80,000 km or as part of major coolant service intervals"],
["P0130","O2 Sensor Circuit Bank 1 Sensor 1",
 "Aged or contaminated upstream oxygen sensor, damaged sensor wiring, or exhaust leak affecting sensor readings",
 "Inspect exhaust system for leaks near the sensor, check wiring and connector condition, and replace the upstream O2 sensor if signal remains faulty",
 "2500-7000","1-2 hours","Medium",
 "Replace oxygen sensors around 80,000-100,000 km and use quality fuel to extend sensor life"],
["P0134","O2 Sensor Circuit No Activity Detected Bank 1 Sensor 1",
 "Failed oxygen sensor no longer switching, open circuit in sensor heater/signal wiring, or exhaust leak diluting sensor readings",
 "Test sensor heater circuit and signal output with a scan tool, repair any open wiring, and replace the O2 sensor if it fails to respond",
 "2500-7000","1-2 hours","Medium",
 "Address exhaust leaks promptly, as they accelerate O2 sensor contamination and failure"],
["P0138","O2 Sensor Circuit High Voltage Bank 1 Sensor 2",
 "Downstream oxygen sensor short to voltage, sensor contamination from oil/coolant intrusion, or a failing sensor stuck at high voltage",
 "Inspect wiring for shorts to power, check for oil or coolant consumption that could contaminate the sensor, and replace the downstream O2 sensor",
 "2500-7000","1-2 hours","Medium",
 "Fix any oil or coolant leaks promptly to prevent sensor contamination"],
["P0141","O2 Sensor Heater Circuit Bank 1 Sensor 2",
 "Failed heater element inside the downstream O2 sensor, blown heater fuse, or damaged heater circuit wiring",
 "Test heater circuit resistance and power supply, repair wiring or fuse as needed, and replace the O2 sensor if the heater element has failed",
 "2500-7000","1-2 hours","Low",
 "Have the O2 sensor heater circuit checked during periodic electrical inspections"],
["P0157","O2 Sensor Circuit Low Voltage Bank 2 Sensor 2",
 "Downstream oxygen sensor on Bank 2 stuck at low voltage due to aging, wiring short to ground, or a lean exhaust condition",
 "Check for exhaust leaks and lean-running conditions upstream, inspect wiring for shorts to ground, and replace the sensor if it remains faulty",
 "2500-7000","1-2 hours","Medium",
 "Diagnose and correct any lean-running conditions before replacing the sensor to avoid repeat failures"],
["P0171","System Too Lean Bank 1",
 "Vacuum leak, dirty or failing MAF sensor, weak fuel pump/low fuel pressure, or clogged fuel injectors causing insufficient fuel delivery on Bank 1",
 "Inspect for vacuum leaks using smoke test, clean/test the MAF sensor, check fuel pressure, and clean or replace injectors as needed; verify fuel trims return to normal",
 "2000-8000","2-3 hours","Medium",
 "Use quality fuel and have injectors cleaned every 30,000-40,000 km to prevent lean fuel trim conditions"],
["P0172","System Too Rich Bank 1",
 "Leaking fuel injector, faulty fuel pressure regulator, contaminated MAF sensor reading low, or a failing O2 sensor sending incorrect feedback",
 "Test fuel injectors for leakage, check fuel pressure regulator operation, clean/test MAF and O2 sensors, and replace faulty components; verify fuel trims normalize",
 "2000-8000","2-3 hours","Medium",
 "Regularly service the fuel injection system and replace air filter on schedule to maintain correct air-fuel mixture"],
["P0175","System Too Rich Bank 2",
 "Leaking injector or faulty fuel pressure regulator on Bank 2, contaminated air/O2 sensors, or a vacuum leak affecting mixture on that bank",
 "Test Bank 2 injectors and fuel pressure regulator, inspect vacuum lines, and replace faulty sensors or injectors; confirm fuel trims are within range after repair",
 "2000-8000","2-3 hours","Medium",
 "Include fuel trim checks in periodic diagnostic scans to catch rich/lean trends early"],
["P0201","Cylinder 1 Injector A Circuit",
 "Open or shorted injector wiring/connector, failed injector coil, or a damaged engine control module driver for Cylinder 1",
 "Inspect and repair injector wiring/connector, test injector coil resistance, and replace the injector if it fails electrical or spray-pattern testing",
 "2500-9000","1-3 hours","Medium",
 "Use quality fuel with adequate injector cleaning additives and avoid running the tank near empty to reduce injector strain"],
["P0217","Engine Coolant Over Temperature Condition",
 "Coolant leakage, radiator blockage or fin damage, failed thermostat stuck closed, weak radiator fan, or a failing water pump causing the engine to overheat",
 "Pressure-test the cooling system to locate leaks, flush or replace a clogged radiator, replace a stuck thermostat, test radiator fan operation, and replace the water pump if it is worn; refill with correct coolant and bleed air from the system",
 "3000-15000","2-5 hours","High",
 "Check coolant level and condition monthly, flush and replace coolant every 2 years or per manufacturer schedule, and address any overheating symptoms immediately to avoid engine damage"],
["P0230","Fuel Pump Primary Circuit",
 "Faulty fuel pump relay, blown fuse, corroded wiring/connector, or a failed fuel pump control circuit in the ECM",
 "Check fuel pump relay and fuse, inspect and repair wiring/connectors for corrosion, and replace the fuel pump relay or repair the control circuit as needed",
 "1500-6000","1-2 hours","High",
 "Periodically inspect fuses and relays in the engine fuse box for corrosion, especially after monsoon exposure"],
["P0300","Random/Multiple Cylinder Misfire Detected",
 "Worn spark plugs/ignition coils, vacuum leaks, low fuel pressure, or contaminated fuel causing misfires across multiple cylinders",
 "Inspect and replace worn spark plugs and ignition coils, check for vacuum leaks, test fuel pressure and injector spray pattern, and clear codes to confirm the misfire is resolved",
 "3000-12000","2-4 hours","High",
 "Replace spark plugs at manufacturer-specified intervals (typically 30,000-40,000 km) and use good quality fuel to prevent injector fouling"],
["P0301","Cylinder 1 Misfire Detected",
 "Faulty spark plug or ignition coil on Cylinder 1, a leaking or clogged injector, or low compression from a worn piston ring or valve",
 "Swap coil/plug with another cylinder to isolate the fault, replace faulty ignition components, test injector function, and perform a compression test if misfire persists",
 "2000-9000","1-3 hours","High",
 "Inspect spark plugs and coils during regular service intervals and address any rough-idle symptoms early to avoid catalytic converter damage"],
["P0304","Cylinder 4 Misfire Detected",
 "Faulty spark plug or ignition coil on Cylinder 4, injector fault, or low cylinder compression from valve/piston wear",
 "Swap coil/plug to isolate the fault, replace faulty ignition components or injector, and run a compression test if the misfire continues after ignition repairs",
 "2000-9000","1-3 hours","High",
 "Replace ignition coils and plugs together as a set when one fails, since neighbouring coils are often at similar wear levels"],
["P0325","Knock/Combustion Vibration Sensor A Circuit",
 "Damaged knock sensor wiring, loose sensor mounting torque, or a failed knock sensor no longer detecting engine vibration correctly",
 "Inspect wiring and connector for damage, verify sensor mounting torque, and replace the knock sensor if it fails resistance/output testing",
 "2000-6000","1-2 hours","Medium",
 "Use the manufacturer-recommended fuel octane rating to reduce engine knock and sensor stress"],
["P0335","Crankshaft Position Sensor A Circuit",
 "Damaged crankshaft position sensor, worn reluctor ring/tone wheel, or wiring damage causing loss of crank signal",
 "Inspect wiring and connector, check the reluctor ring for damage, and replace the crankshaft position sensor; this fault can cause a no-start and should be addressed promptly",
 "2000-7000","1-2 hours","High",
 "Keep the sensor area free of oil contamination, which can cause premature sensor failure"],
["P0339","Crankshaft Position Sensor A Circuit Intermittent",
 "Loose sensor connector, intermittent wiring fault, or a sensor with an inconsistent air gap causing signal dropouts",
 "Secure and clean the sensor connector, inspect wiring for intermittent breaks, and replace the sensor if the intermittent signal persists under road testing",
 "2000-7000","1-2 hours","High",
 "Have wiring harness connectors inspected during services to catch intermittent faults before they cause stalling"],
["P0341","Camshaft Position Sensor A Circuit Range/Performance Bank 1 or Single Sensor",
 "Worn timing chain affecting cam timing, damaged sensor tone wheel, or a failing camshaft position sensor giving an out-of-range signal",
 "Verify cam timing against specification, inspect the sensor and tone wheel for damage, and replace the camshaft position sensor if timing is correct but the signal remains faulty",
 "2500-8000","1-3 hours","Medium",
 "Address timing chain wear promptly, as a stretched chain can trigger camshaft sensor performance codes"],
["P0401","EGR A Flow Insufficient Detected",
 "Carbon-clogged EGR valve or passages, faulty EGR valve actuator, or a blocked EGR cooler restricting exhaust gas flow",
 "Remove and clean the EGR valve and intake passages of carbon deposits, test the EGR valve actuator, and replace the valve or cooler if clogging cannot be cleared",
 "2500-9000","2-3 hours","Medium",
 "Use good quality fuel and have the EGR system inspected and cleaned every 40,000-50,000 km, especially in city stop-go driving"],
["P0420","Catalyst System Efficiency Below Threshold Bank 1",
 "Aging or contaminated catalytic converter, exhaust leak affecting oxygen sensor readings, or an engine misfire/rich condition damaging the catalyst over time",
 "Diagnose and fix any misfire or rich/lean condition first, inspect exhaust for leaks near the sensors, and replace the catalytic converter if it has genuinely degraded",
 "8000-35000","2-4 hours","Medium",
 "Fix engine misfires and oil-burning issues promptly, as they are the leading cause of premature catalytic converter failure"],
["P0442","EVAP System Leak Detected (small leak)",
 "Loose or faulty fuel filler cap, small crack in EVAP hoses, or a leaking purge/vent valve allowing a small vapor leak",
 "Check and tighten or replace the fuel cap first, then smoke-test EVAP hoses and valves to locate and repair the small leak",
 "800-4000","1 hour","Low",
 "Always ensure the fuel cap is tightened until it clicks after refuelling; inspect EVAP hoses periodically for cracking"],
["P0446","EVAP System Vent Control Circuit",
 "Stuck or clogged EVAP vent valve, damaged wiring to the vent solenoid, or debris blocking the vent path",
 "Inspect and clean or replace the EVAP vent control valve, repair wiring as needed, and clear debris from the vent line",
 "1500-5000","1-2 hours","Low",
 "Keep the EVAP vent valve area free of dirt and road debris during under-body inspections"],
["P0449","EVAP System Vent Valve Control Circuit/Open",
 "Open circuit in the EVAP vent valve wiring, blown fuse, or a failed vent valve solenoid",
 "Inspect and repair the open wiring circuit, check the relevant fuse, and replace the EVAP vent valve solenoid if it fails to actuate",
 "1500-5000","1-2 hours","Low",
 "Include EVAP system solenoids in periodic electrical system checks"],
["P0455","EVAP System Leak Detected - Large Leak",
 "Missing, loose, or damaged fuel filler cap, disconnected or cracked large EVAP hose, or a failed purge valve stuck open",
 "Verify the fuel cap is present and sealing correctly, inspect large EVAP hoses and connections for disconnection or cracks, and replace the purge valve if it is stuck open",
 "1000-5000","1 hour","Low",
 "Replace the fuel filler cap if the seal is worn, and check EVAP hose connections during routine servicing"],
["P0480","Fan 1 Control Circuit",
 "Faulty cooling fan relay, blown fuse, damaged fan motor, or wiring fault preventing correct fan control",
 "Check the fan relay and fuse, test fan motor operation directly, and repair wiring or replace the fan motor/relay as needed",
 "2000-8000","1-2 hours","High",
 "Test cooling fan operation each summer before hot weather to catch failures before they cause overheating"],
["P0500","Vehicle Speed Sensor A Circuit",
 "Damaged VSS wiring or connector, worn sensor, or a damaged tone ring/reluctor at the transmission output affecting speed signal",
 "Inspect wiring and connector for damage, check the sensor and tone ring, and replace the vehicle speed sensor if it fails to produce a correct signal",
 "1500-5000","1-2 hours","Medium",
 "Have the speed sensor and wiring inspected if speedometer or cruise control behaves erratically"],
["P0505","Idle Control System",
 "Carbon buildup in the throttle body/idle air passage, faulty idle air control valve, or a vacuum leak affecting idle stability",
 "Clean the throttle body and idle air passages, test and replace the idle air control valve if faulty, and check for vacuum leaks affecting idle",
 "1500-6000","1-2 hours","Medium",
 "Clean the throttle body and idle control passages every 20,000-25,000 km to prevent carbon-related idle issues"],
["P0507","Idle Control System RPM - Higher Than Expected",
 "Vacuum leak allowing unmetered air into the intake, stuck-open idle air control valve, or a throttle body carbon deposit holding the throttle plate open",
 "Inspect for vacuum leaks with a smoke test, clean or replace the idle air control valve, and clean the throttle body to restore normal idle RPM",
 "1500-6000","1-2 hours","Medium",
 "Address any vacuum leaks promptly, as they affect both idle quality and fuel trim accuracy"],
["P0521","Engine Oil Pressure Sensor/Switch A Range/Performance",
 "Faulty oil pressure sensor/switch giving an inaccurate reading, or clogged sensor port from sludge buildup",
 "Verify actual oil pressure with a mechanical gauge to rule out a real oil pressure problem, clean the sensor port, and replace the oil pressure sensor/switch if it reads incorrectly",
 "1000-3500","1 hour","Medium",
 "Change engine oil and filter on schedule to prevent sludge buildup that can affect the oil pressure sensor port"],
["P0522","Engine Oil Pressure Sensor/Switch A Low",
 "Low actual engine oil level/pressure, worn oil pump, or a failed oil pressure sensor reading falsely low",
 "First check oil level and top up if low; if oil level is correct, verify actual oil pressure with a mechanical gauge, and replace the oil pump or sensor as indicated by testing",
 "1200-9000","1-3 hours","High",
 "Check engine oil level monthly and never drive with a confirmed low oil pressure warning, as this can cause severe engine damage"],
["P0562","System Voltage Low",
 "Weak or failing battery, loose/corroded battery terminals, or a faulty alternator not charging sufficiently",
 "Test battery condition and charge, clean and tighten battery terminals, and test alternator output; replace the battery or alternator as needed",
 "3000-12000","1-2 hours","High",
 "Have the battery and alternator load-tested every 12 months and clean terminals periodically to prevent corrosion-related voltage drops"],
["P0563","System Voltage High",
 "Faulty voltage regulator within the alternator causing overcharging, or a damaged battery sensor circuit",
 "Test alternator output voltage under load, replace the alternator or voltage regulator if overcharging is confirmed, and inspect the battery for damage from overcharging",
 "4000-14000","1-2 hours","High",
 "Have charging system voltage checked during periodic services to catch a failing regulator before it damages the battery or electronics"],
["P0603","Internal Control Module Keep Alive Memory (KAM) Error",
 "Loss of continuous battery power to the ECM from a blown fuse or wiring fault, or an internal ECM memory fault",
 "Check fuses and wiring supplying constant power to the ECM, repair any faults found, and reprogram or replace the ECM if the internal memory fault persists",
 "3000-20000","1-3 hours","Medium",
 "Avoid disconnecting the battery unnecessarily and ensure battery terminals remain clean and tight to prevent power interruptions to the ECM"],
["P0606","Control Module Processor",
 "Internal ECM processor fault, often caused by voltage spikes, water intrusion, or component aging within the control module",
 "Inspect for water intrusion at the ECM connector, check for recent electrical faults or jump-start damage, and reprogram or replace the ECM if the internal fault is confirmed",
 "8000-30000","2-4 hours","High",
 "Protect the ECM connector from water exposure and avoid incorrect jump-starting procedures that can cause voltage spikes"],
["P0700","Transmission Control System (MIL Request)",
 "A fault detected within the transmission control module has requested the check engine light; the specific transmission fault code must be retrieved separately",
 "Scan the transmission control module for the specific stored fault code, diagnose and repair the underlying transmission issue identified, and clear codes once resolved",
 "3000-25000","2-6 hours","High",
 "Service the transmission fluid and filter per manufacturer schedule (typically every 40,000-60,000 km) to prevent transmission-related faults"],
["P0715","Input/Turbine Shaft Speed Sensor A Circuit",
 "Damaged input speed sensor wiring, worn sensor, or contamination from transmission fluid debris affecting the sensor",
 "Inspect wiring and connector, check transmission fluid condition for excessive debris, and replace the input speed sensor if it fails testing",
 "3000-10000","2-3 hours","High",
 "Change transmission fluid and filter on schedule to reduce debris contamination affecting internal sensors"],
["P0720","Output Shaft Speed Sensor Circuit",
 "Damaged output speed sensor wiring, worn sensor, or debris contamination in the transmission affecting sensor signal",
 "Inspect wiring and connector, check transmission fluid condition, and replace the output speed sensor if faulty",
 "3000-10000","2-3 hours","High",
 "Maintain clean transmission fluid through scheduled services to protect internal speed sensors"],
["P0731","Gear 1 Incorrect Ratio",
 "Worn clutch packs or bands within the transmission, low or degraded transmission fluid, or a faulty solenoid affecting gear 1 engagement",
 "Check transmission fluid level and condition first, test shift solenoids, and have the transmission internally inspected/repaired if clutch or band wear is confirmed",
 "8000-40000","3-8 hours","High",
 "Service transmission fluid at manufacturer-recommended intervals and avoid aggressive driving that accelerates clutch wear"],
["P0740","Torque Converter Clutch Circuit/Open",
 "Open circuit in the torque converter clutch solenoid wiring, blown fuse, or a failed TCC solenoid",
 "Inspect and repair the TCC solenoid wiring and connector, check the relevant fuse, and replace the torque converter clutch solenoid if it fails to actuate",
 "3500-15000","2-4 hours","Medium",
 "Include transmission solenoid checks during major services, especially if shuddering is felt during highway cruising"],
]

REPAIR_HEADER = ["OBD_Code", "Description", "Cause", "Solution",
                  "Estimated_Cost_INR", "Repair_Time", "Severity",
                  "Preventive_Maintenance"]


def build_repair_knowledge(output_path: str) -> int:
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(REPAIR_HEADER)
        writer.writerows(REPAIR_ROWS)
    return len(REPAIR_ROWS)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate AutoIntel AI Week 1 datasets")
    parser.add_argument("--input", default="obd_codes_clean.csv",
                         help="Path to the raw obd_codes_clean.csv file")
    parser.add_argument("--outdir", default="out",
                         help="Directory to write output CSVs to")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    obd_out = os.path.join(args.outdir, "obd_knowledge.csv")
    repair_out = os.path.join(args.outdir, "repair_knowledge.csv")

    n_obd = clean_obd_dataset(args.input, obd_out)
    print(f"obd_knowledge.csv written: {n_obd} rows -> {obd_out}")

    n_repair = build_repair_knowledge(repair_out)
    print(f"repair_knowledge.csv written: {n_repair} rows -> {repair_out}")


if __name__ == "__main__":
    main()
