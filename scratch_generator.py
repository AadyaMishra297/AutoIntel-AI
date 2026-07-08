import os

base_data = {
    'Engine Overheating': {
        'obd_code': 'P0217', 'category': 'Engine Cooling',
        'keywords': ['overheat', 'hot', 'temperature', 'coolant', 'radiator', 'steam', 'boil', 'thermostat', 'water pump', 'gauge red', 'hissing']
    },
    'Battery and Charging Fault': {
        'obd_code': 'P0620', 'category': 'Electrical',
        'keywords': ['battery', 'alternator', 'charge', 'dead', 'crank', 'jump start', 'terminals', 'voltage', 'electrical', 'dim lights', 'wont start']
    },
    'Fuel System Pressure Low': {
        'obd_code': 'P0087', 'category': 'Fuel System',
        'keywords': ['fuel', 'pressure', 'pump', 'injector', 'stutter', 'starve', 'gas', 'stall', 'hesitate', 'sluggish', 'power loss']
    },
    'Oxygen Sensor Fault': {
        'obd_code': 'P0131', 'category': 'Emissions and Exhaust',
        'keywords': ['oxygen', 'sensor', 'o2', 'lambda', 'emissions', 'exhaust', 'rich', 'lean', 'smell', 'unburnt', 'fuel trim', 'catalytic']
    },
    'Brake System Fault': {
        'obd_code': 'P0571', 'category': 'Brakes',
        'keywords': ['brake', 'pad', 'rotor', 'caliper', 'fluid', 'pedal', 'squeal', 'grind', 'spongy', 'stop', 'disc']
    },
    'Transmission Fault': {
        'obd_code': 'P0700', 'category': 'Transmission',
        'keywords': ['transmission', 'gear', 'shift', 'slip', 'clutch', 'automatic', 'manual', 'torque', 'converter', 'jerk', 'fluid red']
    },
    'Engine Misfire': {
        'obd_code': 'P0300', 'category': 'Engine',
        'keywords': ['misfire', 'spark', 'plug', 'coil', 'cylinder', 'shake', 'vibrate', 'rough idle', 'buck', 'surge', 'ignition']
    },
    'Air Conditioning Failure': {
        'obd_code': 'P0533', 'category': 'HVAC',
        'keywords': ['air conditioning', 'ac', 'compressor', 'refrigerant', 'freon', 'warm air', 'cool', 'hvac', 'vent', 'blows hot', 'condenser']
    },
    'ABS Wheel Speed Sensor Fault': {
        'obd_code': 'P0500', 'category': 'ABS and Traction Control',
        'keywords': ['abs', 'wheel', 'speed', 'sensor', 'traction', 'anti-lock', 'skid', 'slip warning', 'stability', 'yaw', 'tone ring']
    },
    'Steering and Suspension Fault': {
        'obd_code': 'P0563', 'category': 'Steering and Suspension',
        'keywords': ['steering', 'suspension', 'strut', 'shock', 'tie rod', 'pull', 'wander', 'clunk', 'alignment', 'power steering', 'wheel bearing']
    }
}

prefixes = ['I have a problem with', 'My car has', 'Experiencing', 'Noticed that', 'The mechanic said', 'Dashboard shows', 'Warning light for', 'Lately my vehicle has', 'There is an issue with']
suffixes = ['while driving.', 'when I start the car.', 'on the highway.', 'in the morning.', 'recently.', 'and it is getting worse.', 'which is dangerous.', 'every time I drive.', '']

complaints_py = 'import pandas as pd\nimport os\n\nFAULT_COMPLAINTS = {\n'

for fault, data in base_data.items():
    complaints_py += f'    "{fault}": {{\n'
    complaints_py += f'        "obd_code": "{data["obd_code"]}",\n'
    complaints_py += f'        "category": "{data["category"]}",\n'
    complaints_py += f'        "complaints": [\n'
    
    count = 0
    for k1 in data['keywords']:
        for k2 in data['keywords']:
            if k1 != k2 and count < 40:
                p = prefixes[count % len(prefixes)]
                s = suffixes[count % len(suffixes)]
                sentence = f"{p} {k1} and {k2} {s}".strip()
                complaints_py += f'            "{sentence}",\n'
                count += 1
    
    complaints_py += f'        ],\n    }},\n'

complaints_py += '}\n\n'
complaints_py += 'OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "knowledge", "complaint_dataset.csv")\n\n'
complaints_py += 'def generate_complaint_dataset():\n'
complaints_py += '    records = []\n    counter = 1\n'
complaints_py += '    for fault_name, info in FAULT_COMPLAINTS.items():\n'
complaints_py += '        for complaint_text in info["complaints"]:\n'
complaints_py += '            records.append({"complaint_id": f"C{counter:03d}", "complaint_text": complaint_text, "fault_name": fault_name, "obd_code": info["obd_code"], "fault_category": info["category"]})\n'
complaints_py += '            counter += 1\n'
complaints_py += '    df = pd.DataFrame(records)\n'
complaints_py += '    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)\n'
complaints_py += '    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")\n'
complaints_py += '    return df\n\n'
complaints_py += 'if __name__ == "__main__":\n'
complaints_py += '    df = generate_complaint_dataset()\n'
complaints_py += '    print(f"Dataset generated: {len(df)} rows")\n'

with open('src/analysis/complaint_dataset.py', 'w') as f:
    f.write(complaints_py)
