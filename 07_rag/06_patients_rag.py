# 06_patients_rag.py
# Custom RAG workflow: SQLite patients.db + Ollama (LAB_custom_rag_query.md)
# Tim Fraser (pattern); clinical retrieval + YAML-grounded system prompt.

# Retrieves structured rows from SQLite, passes them as JSON to the LLM for
# professional synopsis only—counts and filters come from SQL, not the model.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import argparse
import json
import os
import runpy
import sqlite3
from typing import Optional

import pandas as pd

try:
    import yaml
except ImportError:
    yaml = None  # optional; see load_rules()

from functions import agent_run

## 0.2 Working directory (script folder) #################################

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

## 0.3 Start Ollama (same pattern as 04_sqlite.py) #################################

ollama_script_path = os.path.join(script_dir, "01_ollama.py")
_ = runpy.run_path(ollama_script_path)

## 0.4 Configuration #################################

MODEL = "gemma3"
PORT = 11434
OLLAMA_HOST = f"http://localhost:{PORT}"
DB_PATH = os.path.join(script_dir, "patients.db")
RULES_PATH = os.path.join(script_dir, "clinical_rag_rules.yaml")

# 1. LOAD YAML RULES → SYSTEM PROMPT STRING ###################################


def load_rules(path: str) -> str:
    """
    Build a single system prompt from clinical_rag_rules.yaml.
    Falls back to a short inline prompt if PyYAML is not installed.
    """
    if yaml is None or not os.path.isfile(path):
        return (
            "You are a clinical documentation assistant. Summarize ONLY the JSON "
            "facts in the user message. Do not invent names, dates, scores, or counts. "
            "If data are missing, say so. Professional, concise tone."
        )
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    parts = []
    if cfg.get("metadata", {}).get("data_notice"):
        parts.append("Data notice: " + cfg["metadata"]["data_notice"].strip())
    if cfg.get("style"):
        s = cfg["style"]
        parts.append(
            f"Style: {s.get('tone', '')}. Language: {s.get('language', '')}. "
            f"Format: {s.get('format_preference', '')}."
        )
    for key in ("accuracy", "hallucination_prevention", "clinical_safety", "privacy"):
        items = cfg.get(key)
        if isinstance(items, list):
            parts.append(key.upper().replace("_", " ") + ":")
            for line in items:
                parts.append(f"- {line}")
    return "\n".join(parts)


SYSTEM_PROMPT = load_rules(RULES_PATH)

# LLM instruction for Q4 (lapsed follow-up + cohort stats in JSON)
Q4_TASK = (
    "Summarize overdue follow-up for this cohort using ONLY retrieval and "
    "summary_statistics. Include: (1) how many patients and notable names/IDs if helpful; "
    "(2) diagnosis_counts_at_last_visit — describe distribution with exact counts; "
    "(3) mean_days_since_last_visit and median_days_since_last_visit from summary_statistics; "
    "(4) last_visit_provider_counts — if all_lapsed_patients_share_same_last_provider is true, "
    "clearly flag that single provider by name; otherwise highlight the most common last-visit "
    "providers. Do not invent numbers or providers not in the JSON."
)

# 2. SEARCH / RETRIEVAL FUNCTIONS (SQLite) ###################################


def get_connection():
    """Open SQLite connection to patients.db."""
    if not os.path.isfile(DB_PATH):
        raise FileNotFoundError(
            f"Missing {DB_PATH}. Run fakerdata.py from the 07_rag folder first."
        )
    return sqlite3.connect(DB_PATH)


def retrieve_provider_patient_count(conn: sqlite3.Connection, provider: str) -> pd.DataFrame:
    """
    Distinct patients who have at least one visit with the given provider.
    """
    sql = """
    SELECT COUNT(DISTINCT patient_id) AS distinct_patient_count
    FROM visits
    WHERE provider = ?
    """
    return pd.read_sql_query(sql, conn, params=(provider,))


def retrieve_patient_care_records(conn: sqlite3.Connection, patient_id: int) -> pd.DataFrame:
    """Patient demographics + all visits for synopsis."""
    sql = """
    SELECT
      p.id AS patient_id,
      p.name AS patient_name,
      p.date_of_birth AS date_of_birth,
      v.id AS visit_id,
      v.visit_date,
      v.phq9_score,
      v.safety_concerns,
      v.diagnosis,
      v.provider,
      v.medications
    FROM patients p
    LEFT JOIN visits v ON v.patient_id = p.id
    WHERE p.id = ?
    ORDER BY v.visit_date
    """
    return pd.read_sql_query(sql, conn, params=(patient_id,))


def retrieve_high_risk_phq9(conn: sqlite3.Connection, threshold: int = 15) -> pd.DataFrame:
    """Visits with PHQ-9 strictly greater than threshold (e.g., high symptom burden)."""
    sql = """
    SELECT
      p.id AS patient_id,
      p.name AS patient_name,
      v.visit_date,
      v.phq9_score,
      v.diagnosis,
      v.provider,
      v.safety_concerns
    FROM visits v
    JOIN patients p ON p.id = v.patient_id
    WHERE v.phq9_score > ?
    ORDER BY v.phq9_score DESC, v.visit_date DESC
    """
    return pd.read_sql_query(sql, conn, params=(threshold,))


def retrieve_not_seen_days(conn: sqlite3.Connection, min_days: int = 60) -> pd.DataFrame:
    """
    Patients whose most recent visit is more than min_days before today (ISO dates).
    Includes diagnosis and provider from that last visit for cohort summaries.
    """
    sql = """
    SELECT
      p.id AS patient_id,
      p.name AS patient_name,
      v.visit_date AS last_visit_date,
      v.diagnosis AS last_visit_diagnosis,
      v.provider AS last_visit_provider,
      CAST(julianday('now') - julianday(v.visit_date) AS INTEGER) AS days_since_last_visit
    FROM patients p
    JOIN visits v ON v.patient_id = p.id
    WHERE v.id = (
      SELECT v2.id FROM visits v2
      WHERE v2.patient_id = p.id
      ORDER BY v2.visit_date DESC, v2.id DESC
      LIMIT 1
    )
    AND CAST(julianday('now') - julianday(v.visit_date) AS INTEGER) > ?
    ORDER BY last_visit_date ASC
    """
    return pd.read_sql_query(sql, conn, params=(min_days,))


def summarize_lapsed_cohort(df: pd.DataFrame) -> dict:
    """
    Aggregate stats for patients overdue for follow-up (computed in Python/SQL, not the LLM).
    """
    if df.empty:
        return {
            "patient_count": 0,
            "mean_days_since_last_visit": None,
            "median_days_since_last_visit": None,
            "diagnosis_counts_at_last_visit": {},
            "last_visit_provider_counts": {},
            "all_lapsed_patients_share_same_last_provider": False,
            "single_last_provider_name_if_applicable": None,
            "note": "Empty cohort.",
        }

    mean_d = float(df["days_since_last_visit"].mean())
    med_d = float(df["days_since_last_visit"].median())
    diag_counts = {
        str(k): int(v) for k, v in df["last_visit_diagnosis"].value_counts().items()
    }
    prov_counts = {
        str(k): int(v) for k, v in df["last_visit_provider"].value_counts().items()
    }
    n_unique = df["last_visit_provider"].nunique()
    single_provider = n_unique == 1
    single_name = str(df["last_visit_provider"].iloc[0]) if single_provider else None

    return {
        "patient_count": int(len(df)),
        "mean_days_since_last_visit": round(mean_d, 1),
        "median_days_since_last_visit": round(med_d, 1),
        "diagnosis_counts_at_last_visit": diag_counts,
        "last_visit_provider_counts": prov_counts,
        "all_lapsed_patients_share_same_last_provider": bool(single_provider),
        "single_last_provider_name_if_applicable": single_name,
        "note": (
            "mean/median days_since_last_visit summarize how long each patient's last "
            "documented visit was ago (follow-up gap). This is not a count of missed appointments."
        ),
    }


# 3. RAG: RETRIEVAL JSON + LLM SYNOPSIS ###################################


def rag_synopsis(
    role: str,
    task_label: str,
    df: pd.DataFrame,
    model: str = MODEL,
    summary_statistics: Optional[dict] = None,
) -> str:
    """
    Pass retrieval as JSON; ask model for a synopsis grounded in that payload only.
    Optional summary_statistics (e.g. cohort aggregates) are included when provided.
    """
    payload = {
        "task": task_label,
        "retrieval": df.to_dict(orient="records"),
        "row_count": len(df),
    }
    if summary_statistics is not None:
        payload["summary_statistics"] = summary_statistics
    task_json = json.dumps(payload, indent=2)
    return agent_run(role=role, task=task_json, model=model, output="text")


def demo_pick_provider(conn: sqlite3.Connection) -> str:
    """One provider from DB for the demo query."""
    row = conn.execute(
        "SELECT provider FROM visits ORDER BY provider LIMIT 1"
    ).fetchone()
    return row[0] if row else "Dr. Nobody"


def demo_pick_patient_id(conn: sqlite3.Connection) -> int:
    """First patient id for demo synopsis."""
    row = conn.execute("SELECT id FROM patients ORDER BY id LIMIT 1").fetchone()
    return int(row[0]) if row else 1


def run_all_demos(
    conn: sqlite3.Connection,
    model: str,
    provider: Optional[str] = None,
    patient_id: Optional[int] = None,
) -> None:
    """Run four lab queries: retrieval + LLM synopsis for each."""
    provider = provider or demo_pick_provider(conn)
    pid = patient_id if patient_id is not None else demo_pick_patient_id(conn)

    # --- Q1: provider census ---
    df1 = retrieve_provider_patient_count(conn, provider)
    print("=" * 60)
    print("Q1: How many distinct patients does a given provider have?")
    print(f"    (demo provider: {provider})")
    print("SQL retrieval:", df1.to_dict(orient="records"))
    out1 = rag_synopsis(
        SYSTEM_PROMPT,
        "Summarize how many distinct patients are associated with the specified provider "
        "using ONLY the retrieval. One short paragraph plus a bullet with the count.",
        df1,
        model=model,
    )
    print(out1)
    print()

    # --- Q2: one patient synopsis ---
    df2 = retrieve_patient_care_records(conn, pid)
    print("=" * 60)
    print("Q2: Synopsis of care for one patient")
    print(f"    (demo patient_id: {pid})")
    out2 = rag_synopsis(
        SYSTEM_PROMPT,
        "Provide a brief, professional synopsis of this patient's care trajectory "
        "using ONLY the retrieval (visits, PHQ-9, diagnoses, meds). "
        "If there are no visits, say so.",
        df2,
        model=model,
    )
    print(out2)
    print()

    # --- Q3: PHQ-9 > 15 ---
    df3 = retrieve_high_risk_phq9(conn, threshold=15)
    print("=" * 60)
    print("Q3: High-risk visits (PHQ-9 > 15) — synopsis of this cohort")
    print(f"    (rows retrieved: {len(df3)})")
    out3 = rag_synopsis(
        SYSTEM_PROMPT,
        "Summarize this search: list themes (e.g., how many rows, date spread) using "
        "ONLY the retrieval. Do not invent totals beyond row_count and the records.",
        df3,
        model=model,
    )
    print(out3)
    print()

    # --- Q4: not seen in > 60 days (with cohort summary stats in JSON) ---
    df4 = retrieve_not_seen_days(conn, min_days=60)
    lapsed_summary = summarize_lapsed_cohort(df4)
    print("=" * 60)
    print("Q4: Patients not seen in over 60 days (since last visit)")
    print(f"    (rows retrieved: {len(df4)})")
    print(
        "    cohort aggregates (in JSON to LLM): mean_days="
        f"{lapsed_summary.get('mean_days_since_last_visit')}, "
        f"median_days={lapsed_summary.get('median_days_since_last_visit')}, "
        f"same_last_provider_all={lapsed_summary.get('all_lapsed_patients_share_same_last_provider')}"
    )
    out4 = rag_synopsis(
        SYSTEM_PROMPT,
        Q4_TASK,
        df4,
        model=model,
        summary_statistics=lapsed_summary,
    )
    print(out4)
    print()


# 4. CLI: demo vs interactive parameters ###################################


def main():
    parser = argparse.ArgumentParser(
        description="Clinical RAG on patients.db: SQL retrieval + Ollama synopsis."
    )
    parser.add_argument(
        "--mode",
        choices=("demo", "interactive"),
        default="demo",
        help=(
            "demo: run all four queries (optional --provider / --patient-id). "
            "interactive: prompts for provider and patient id for Q1–Q2, then runs Q3–Q4."
        ),
    )
    parser.add_argument("--model", default=MODEL, help="Ollama model name")
    parser.add_argument(
        "--provider",
        default=None,
        help="Provider name for Q1 (exact match to visits.provider); demo picks one if omitted",
    )
    parser.add_argument(
        "--patient-id",
        type=int,
        default=None,
        help="Patient id for Q2; demo uses first patient if omitted",
    )
    args = parser.parse_args()

    conn = get_connection()
    try:
        if args.mode == "interactive":
            print("Interactive mode: enter values (blank uses demo defaults).")
            prov = input("Provider name for Q1 (e.g. Dr. Smith): ").strip() or demo_pick_provider(
                conn
            )
            df1 = retrieve_provider_patient_count(conn, prov)
            print("\n--- Q1 ---\n", rag_synopsis(SYSTEM_PROMPT, "Q1", df1, args.model))
            pid_s = input("Patient id for Q2: ").strip()
            pid = int(pid_s) if pid_s else demo_pick_patient_id(conn)
            df2 = retrieve_patient_care_records(conn, pid)
            print("\n--- Q2 ---\n", rag_synopsis(SYSTEM_PROMPT, "Q2", df2, args.model))
            df3 = retrieve_high_risk_phq9(conn, 15)
            print("\n--- Q3 ---\n", rag_synopsis(SYSTEM_PROMPT, "Q3", df3, args.model))
            df4 = retrieve_not_seen_days(conn, 60)
            s4 = summarize_lapsed_cohort(df4)
            print(
                "\n--- Q4 ---\n",
                rag_synopsis(
                    SYSTEM_PROMPT,
                    Q4_TASK,
                    df4,
                    args.model,
                    summary_statistics=s4,
                ),
            )
        else:
            run_all_demos(
                conn,
                args.model,
                provider=args.provider,
                patient_id=args.patient_id,
            )
    finally:
        conn.close()


if __name__ == "__main__":
    main()
