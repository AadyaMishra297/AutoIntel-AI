import pandas as pd
import numpy as np

# Reproducible randomness -> anyone on the team re-running this script gets
# the identical vehicle_master.csv and the identical FK assignment. This
# matters for SQL re-imports and for git-diffing the CSV during PR review.
RNG = np.random.default_rng(seed=42)

SRC_MAINTENANCE = "/mnt/user-data/uploads/vehicle_maintenance_clean.csv"
OUT_MASTER = "/mnt/user-data/outputs/vehicle_master.csv"
OUT_MAINTENANCE_LINKED = "/mnt/user-data/outputs/vehicle_maintenance_clean_with_id.csv"

# ---------------------------------------------------------------------------
# STEP 1 — Load the cleaned maintenance dataset just to read off the exact
# categorical vocabulary it uses. Hard-coding these elsewhere risks typos
# ("Suv" vs "SUV") that would silently break the SQL join later, so we pull
# them directly from the source of truth.
# ---------------------------------------------------------------------------
maint = pd.read_csv(SRC_MAINTENANCE)

VEHICLE_MODELS = sorted(maint["vehicle_model"].unique())   # e.g. Bus, Car, Motorcycle, Suv, Truck, Van
FUEL_TYPES = sorted(maint["fuel_type"].unique())            # Diesel, Electric, Petrol
ENGINE_SIZES = sorted(maint["engine_size"].unique())         # 800, 1000, 1500, 2000, 2500

print("vehicle_model values:", VEHICLE_MODELS)
print("fuel_type values:    ", FUEL_TYPES)
print("engine_size values:  ", ENGINE_SIZES)

# ---------------------------------------------------------------------------
# STEP 2 — Realistic Brand / Model / Variant catalog (Indian market), grouped
# by vehicle_model category. This is the "creative" layer that turns an
# abstract category like "Suv" into something a user actually recognizes in
# the Streamlit vehicle-selection dropdown.
#
# NOTE: engine_size in the source data is a coarse 5-bucket scale
# (800/1000/1500/2000/2500), not literal cc for every vehicle type — e.g. a
# real motorcycle engine is 100-650cc, not 800-2500cc. Rather than invent
# fake data that contradicts the source file, we keep engine_size as the
# join key (so SQL joins stay valid) and add a separate human-readable
# `Engine` column with realistic displacement/battery text for display
# purposes only.
# ---------------------------------------------------------------------------
CATALOG = {
    "Car": [
        ("Maruti Suzuki", "Alto K10", "LXi"),
        ("Maruti Suzuki", "Swift", "VXi"),
        ("Maruti Suzuki", "Baleno", "Zeta"),
        ("Maruti Suzuki", "Dzire", "ZXi"),
        ("Hyundai", "Grand i10 Nios", "Sportz"),
        ("Hyundai", "i20", "Asta"),
        ("Hyundai", "Verna", "SX"),
        ("Tata", "Tiago", "XZ+"),
        ("Tata", "Altroz", "XZ"),
        ("Tata", "Tigor EV", "XZ+"),
        ("Honda", "Amaze", "VX"),
        ("Honda", "City", "ZX"),
        ("Toyota", "Glanza", "V"),
        ("Skoda", "Slavia", "Ambition"),
        ("Volkswagen", "Virtus", "GT"),
    ],
    "Suv": [
        ("Tata", "Nexon", "XZ+"),
        ("Tata", "Punch", "Adventure"),
        ("Tata", "Harrier", "XZA+"),
        ("Mahindra", "XUV300", "W8"),
        ("Mahindra", "XUV700", "AX7"),
        ("Mahindra", "Scorpio-N", "Z8"),
        ("Hyundai", "Venue", "SX"),
        ("Hyundai", "Creta", "SX(O)"),
        ("Hyundai", "Alcazar", "Signature"),
        ("Kia", "Sonet", "GTX+"),
        ("Kia", "Seltos", "GTX+"),
        ("Toyota", "Urban Cruiser Hyryder", "V"),
        ("Toyota", "Fortuner", "Legender"),
        ("MG", "Astor", "Sharp"),
        ("MG", "ZS EV", "Excite"),
    ],
    "Van": [
        ("Maruti Suzuki", "Eeco", "5-Seater"),
        ("Maruti Suzuki", "Omni", "Cargo"),
        ("Tata", "Winger", "Staff"),
        ("Force Motors", "Traveller", "3350"),
        ("Mahindra", "Supro", "Van"),
    ],
    "Bus": [
        ("Tata", "Starbus", "Ultra 918"),
        ("Ashok Leyland", "Viking", "Falcon"),
        ("Eicher", "Skyline Pro", "1015"),
        ("Force Motors", "Traveller", "Mini Bus"),
        ("Mahindra", "Cruzio", "Grande"),
    ],
    "Truck": [
        ("Tata", "Ace Gold", "CX"),
        ("Tata", "407 Gold", "SFC"),
        ("Tata", "Prima", "LX 2830.K"),
        ("Ashok Leyland", "Dost+", "LS"),
        ("Ashok Leyland", "Boss", "1215"),
        ("Mahindra", "Bolero Pickup", "FB"),
        ("Mahindra", "Furio", "7"),
        ("BharatBenz", "1015R", "Rigid Truck"),
    ],
    "Motorcycle": [
        ("Hero", "Splendor Plus", "Self Start"),
        ("Hero", "HF Deluxe", "Drum"),
        ("Bajaj", "Pulsar 150", "Twin Disc"),
        ("Bajaj", "Platina 100", "ES"),
        ("TVS", "Apache RTR 160", "4V"),
        ("TVS", "Sport", "Self Start"),
        ("Royal Enfield", "Classic 350", "Chrome"),
        ("Royal Enfield", "Meteor 350", "Supernova"),
        ("Honda", "Shine", "SP"),
        ("Yamaha", "FZ-S", "V4"),
    ],
}

# Human-readable Engine description per (engine_size bucket, fuel_type).
# Keeps engine_size as the numeric SQL join key while giving the UI
# something realistic to display.
ENGINE_DESC = {
    800:  {"Petrol": "796cc Petrol Engine",  "Diesel": "793cc Diesel Engine",  "Electric": "Electric Motor - 25 kWh Battery"},
    1000: {"Petrol": "998cc Petrol Engine",  "Diesel": "1120cc Diesel Engine", "Electric": "Electric Motor - 35 kWh Battery"},
    1500: {"Petrol": "1497cc Petrol Engine", "Diesel": "1498cc Diesel Engine", "Electric": "Electric Motor - 45 kWh Battery"},
    2000: {"Petrol": "1998cc Petrol Turbo",  "Diesel": "1993cc Diesel Turbo",  "Electric": "Electric Motor - 60 kWh Battery"},
    2500: {"Petrol": "2494cc Petrol Engine", "Diesel": "2494cc Diesel Engine", "Electric": "Electric Motor - 75 kWh Battery"},
}

# ---------------------------------------------------------------------------
# STEP 3 — Build the master records.
#
# We deliberately generate at least one master vehicle for EVERY
# (vehicle_model, fuel_type, engine_size) combination that appears in the
# maintenance dataset. If we skipped a combination, any maintenance row with
# that signature would have no vehicle to link to in Step 4 — an orphaned
# foreign key, which would break a SQL INNER JOIN and silently drop rows.
# We generate 2 vehicles per combination for realistic variety (e.g. two
# different Diesel/1500cc SUVs), landing us at 6 models x 3 fuels x 5 engine
# sizes x 2 = 180 total records, inside the brief's 100-300 target.
# ---------------------------------------------------------------------------
RECORDS_PER_COMBO = 2
records = []
vehicle_id_counter = 1

for model in VEHICLE_MODELS:
    catalog_options = CATALOG[model]
    for fuel in FUEL_TYPES:
        for engine in ENGINE_SIZES:
            for _ in range(RECORDS_PER_COMBO):
                brand, model_name, variant = catalog_options[RNG.integers(0, len(catalog_options))]
                manufacturing_year = int(RNG.integers(2014, 2025))  # 2014-2024 inclusive, realistic used-fleet spread
                vehicle_id = f"VEH{vehicle_id_counter:04d}"
                vehicle_id_counter += 1

                records.append({
                    "Vehicle_ID": vehicle_id,
                    "vehicle_model": model,          # join key -> maintenance.vehicle_model
                    "Brand": brand,
                    "Model": model_name,
                    "Variant": variant,
                    "fuel_type": fuel,                # join key -> maintenance.fuel_type
                    "engine_size": engine,             # join key -> maintenance.engine_size
                    "Engine": ENGINE_DESC[engine][fuel],
                    "Manufacturing_Year": manufacturing_year,
                })

vehicle_master = pd.DataFrame.from_records(records)

# Sanity check: every combination present in the maintenance data must exist
# in vehicle_master, otherwise Step 4's join would produce nulls.
maint_combos = set(map(tuple, maint[["vehicle_model", "fuel_type", "engine_size"]].drop_duplicates().values))
master_combos = set(map(tuple, vehicle_master[["vehicle_model", "fuel_type", "engine_size"]].drop_duplicates().values))
missing = maint_combos - master_combos
assert not missing, f"vehicle_master is missing combos present in maintenance data: {missing}"

print(f"\nvehicle_master.csv: {len(vehicle_master)} records, covering all {len(master_combos)} combos")

# ---------------------------------------------------------------------------
# STEP 4 — Back-fill Vehicle_ID into a copy of the maintenance dataset.
#
# For each service record, we randomly pick one Vehicle_ID from the pool of
# master vehicles sharing that exact (vehicle_model, fuel_type, engine_size)
# signature. Grouping first and sampling per-group (rather than looping row
# by row) keeps this fast even at 50,000 rows.
# ---------------------------------------------------------------------------
id_pool = (
    vehicle_master.groupby(["vehicle_model", "fuel_type", "engine_size"])["Vehicle_ID"]
    .apply(list)
    .to_dict()
)

maint_linked = maint.copy()
assigned_ids = np.empty(len(maint_linked), dtype=object)

for key, group_idx in maint_linked.groupby(["vehicle_model", "fuel_type", "engine_size"]).groups.items():
    pool = id_pool[key]
    chosen = RNG.choice(pool, size=len(group_idx))
    assigned_ids[maint_linked.index.get_indexer(group_idx)] = chosen

maint_linked.insert(0, "Vehicle_ID", assigned_ids)

# ---------------------------------------------------------------------------
# STEP 5 — Write outputs. Original vehicle_maintenance_clean.csv is left
# untouched; the ID-linked version is a separate deliverable.
# ---------------------------------------------------------------------------
import os
os.makedirs("/mnt/user-data/outputs", exist_ok=True)

vehicle_master.to_csv(OUT_MASTER, index=False)
maint_linked.to_csv(OUT_MAINTENANCE_LINKED, index=False)

print(f"\nSaved: {OUT_MASTER}")
print(f"Saved: {OUT_MAINTENANCE_LINKED}")
print(f"\nEach Vehicle_ID in maintenance data now has between "
      f"{maint_linked['Vehicle_ID'].value_counts().min()} and "
      f"{maint_linked['Vehicle_ID'].value_counts().max()} service records "
      f"(avg {maint_linked['Vehicle_ID'].value_counts().mean():.1f}).")
