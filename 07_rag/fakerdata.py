import sqlite3
from faker import Faker
import random
from datetime import date, timedelta

fake = Faker()

conn = sqlite3.connect("patients.db")
cursor = conn.cursor()

# -----------------------
# CREATE TABLES
# -----------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    date_of_birth TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER,
    visit_date TEXT,
    phq9_score INTEGER,
    safety_concerns TEXT,
    diagnosis TEXT,
    provider TEXT,
    medications TEXT,
    FOREIGN KEY(patient_id) REFERENCES patients(id)
)
""")

# -----------------------
# DATA POOLS
# -----------------------

diagnoses = [
    "Major Depressive Disorder",
    "Generalized Anxiety Disorder",
    "Bipolar II Disorder",
    "PTSD",
    "Panic Disorder",
    "ADHD",
    "Obsessive-Compulsive Disorder",
    "Social Anxiety Disorder",
    "Persistent Depressive Disorder"
]

medications = [
    "Sertraline", "Fluoxetine", "Escitalopram", "Venlafaxine",
    "Bupropion", "Mirtazapine", "Lamotrigine", "Lithium",
    "Quetiapine", "Aripiprazole", "Adderall", "Vyvanse"
]

# -----------------------
# HELPERS
# -----------------------

def random_dob():
    today = date.today()
    age = random.randint(18, 80)
    days_old = age * 365 + random.randint(0, 364)
    dob = today - timedelta(days=days_old)
    return dob.isoformat()

def random_visit_date():
    today = date.today()
    days_back = random.randint(0, 365 * 2)  # last 2 years
    visit = today - timedelta(days=days_back)
    return visit.isoformat()

def pick_medications():
    # 0–3 meds per visit
    meds = random.sample(medications, random.randint(0, 3))
    return ", ".join(meds) if meds else "None"

# -----------------------
# GENERATE DATA
# -----------------------

NUM_PATIENTS = 100

for _ in range(NUM_PATIENTS):
    name = fake.name()
    dob = random_dob()

    # Insert patient
    cursor.execute("""
    INSERT INTO patients (name, date_of_birth)
    VALUES (?, ?)
    """, (name, dob))

    patient_id = cursor.lastrowid

    # Each patient gets 1–5 visits
    num_visits = random.randint(1, 5)

    baseline_phq9 = random.randint(5, 25)

    for i in range(num_visits):
        visit_date = random_visit_date()

        # simulate trend (slight improvement or fluctuation)
        phq9 = max(0, min(27, baseline_phq9 + random.randint(-5, 3)))

        safety = "Y" if phq9 >= 20 and random.random() > 0.4 else "N"

        diagnosis = random.choice(diagnoses)
        provider = f"Dr. {fake.last_name()}"
        meds = pick_medications()

        cursor.execute("""
        INSERT INTO visits (
            patient_id, visit_date, phq9_score,
            safety_concerns, diagnosis, provider, medications
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            patient_id, visit_date, phq9,
            safety, diagnosis, provider, meds
        ))

conn.commit()

# -----------------------
# QUICK CHECK
# -----------------------

cursor.execute("""
SELECT p.name, v.visit_date, v.phq9_score, v.medications
FROM patients p
JOIN visits v ON p.id = v.patient_id
LIMIT 5
""")

rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()

print("\n✅ Created patients.db with patients + visits + medications")