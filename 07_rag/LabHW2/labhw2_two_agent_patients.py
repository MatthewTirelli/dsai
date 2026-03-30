# labhw2_two_agent_patients.py
# LabHW2: Custom tool + two-agent workflow (PHQ-9 and safety flags)
# Uses local functions.py in this folder (no imports from 08_function_calling).

# Task 1: Custom SQLite tool + tool metadata for cohort query.
# Task 2: Agent 1 calls the tool; Agent 2 writes a one-page clinical synopsis from the cohort.
# Task 3: Run, then refine tool descriptions or prompts as needed.

# 0. SETUP ###################################

## 0.1 Load Packages ############################

import sqlite3  # for querying patients.db
import sys
from pathlib import Path

import pandas as pd  # for data manipulation

# If you haven't already, install these packages...
# pip install pandas requests tabulate

## 0.2 Import helpers from this folder ############################

# Allow `python path/to/labhw2_two_agent_patients.py` from any working directory
LAB_DIR = Path(__file__).resolve().parent
if str(LAB_DIR) not in sys.path:
    sys.path.insert(0, str(LAB_DIR))

from functions import OLLAMA_HOST, agent_run, df_as_text  # noqa: E402

## 0.3 Configuration ############################

# Use a model you have pulled (`ollama list`). Run: ollama pull llama3.2
MODEL = "llama3.2"
DB_PATH = LAB_DIR / "patients.db"
OUT_SYNOPSIS = LAB_DIR / "clinical_findings_synopsis.md"
OUT_AGENT1 = LAB_DIR / "agent1_cohort_findings.md"

# PHQ-9 strictly above 15 (i.e., scores 16+)
PHQ9_MIN_EXCLUSIVE = 15

# 1. CUSTOM TOOL ###################################

def list_phq9_elevated_with_safety_concerns(**_kwargs):
    """
    Return visits where PHQ-9 is above the threshold and safety_concerns is Y.

    Always reads LabHW2/patients.db next to this script. Extra tool arguments from
    the model are ignored so a bad db_path cannot open an empty SQLite file (which
    would raise "no such table: visits").

    Returns
    -------
    pandas.DataFrame
        One row per qualifying visit with patient demographics and visit fields.
    """
    path = str(DB_PATH.resolve())

    sql = """
    SELECT
        p.id AS patient_id,
        p.name AS patient_name,
        p.date_of_birth,
        v.id AS visit_id,
        v.visit_date,
        v.phq9_score,
        v.safety_concerns,
        v.diagnosis,
        v.provider,
        v.medications
    FROM visits v
    INNER JOIN patients p ON p.id = v.patient_id
    WHERE v.phq9_score > ?
      AND UPPER(TRIM(COALESCE(v.safety_concerns, ''))) = 'Y'
    ORDER BY v.visit_date DESC, p.id ASC;
    """

    with sqlite3.connect(path) as conn:
        df = pd.read_sql_query(sql, conn, params=(PHQ9_MIN_EXCLUSIVE,))

    return df


tool_list_phq9_safety = {
    "type": "function",
    "function": {
        "name": "list_phq9_elevated_with_safety_concerns",
        "description": (
            "Query the Lab patients database and return a table of visits where "
            "PHQ-9 score is greater than 15 (16 or higher) and safety_concerns is 'Y'. "
            "Each row is one visit with patient name, DOB, visit date, scores, "
            "diagnosis, provider, and medications. Call with an empty argument object {}."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
}

AGENT1_TOOL_NAME = tool_list_phq9_safety["function"]["name"]
# Ollama: force this exact tool (needs a tool-capable model + recent Ollama).
AGENT1_TOOL_CHOICE = {"type": "function", "function": {"name": AGENT1_TOOL_NAME}}


def _coerce_tool_result_to_dataframe(result):
    """
    With output='text', agent_run returns the last tool's return value (a DataFrame).
    With output='tools', the return value is a list of tool_calls dicts with 'output'.
    """
    if isinstance(result, pd.DataFrame):
        return result
    if isinstance(result, list) and result:
        first = result[0]
        if isinstance(first, dict) and isinstance(first.get("output"), pd.DataFrame):
            return first["output"]
        last = result[-1]
        if isinstance(last, dict) and isinstance(last.get("output"), pd.DataFrame):
            return last["output"]
    return None


# 2. TWO-AGENT WORKFLOW ###################################

print("Starting LabHW2 workflow…", flush=True)
print(f"Ollama base URL: {OLLAMA_HOST} (override with env OLLAMA_HOST if needed)", flush=True)
print(f"Ollama model: {MODEL} (ensure `ollama serve` is running and the model is pulled)", flush=True)
print("Calling Agent 1 (tool cohort) — this can take a while on first load…", flush=True)

role1 = (
    "You are a clinical data assistant. You may ONLY satisfy requests by calling the "
    f"provided tool `{AGENT1_TOOL_NAME}`. Call it exactly once with arguments: {{}} "
    "(empty JSON object). Do not reply with prose, lists, or invented patients."
)
task1 = (
    "Pull every visit where PHQ-9 is above 15 and safety_concerns is Y. "
    f"Call `{AGENT1_TOOL_NAME}` with {{}}."
)

raw1 = agent_run(
    role=role1,
    task=task1,
    model=MODEL,
    tools=[tool_list_phq9_safety],
    output="text",
    tool_choice=AGENT1_TOOL_CHOICE,
)

coerced_df = _coerce_tool_result_to_dataframe(raw1)
if coerced_df is None:
    preview = ""
    if isinstance(raw1, str) and raw1.strip():
        preview = raw1.strip()[:400].replace("\n", " ")
    raise SystemExit(
        "\nAssignment requirement: Agent 1 must return data via the registered tool.\n"
        f"Expected tool: {AGENT1_TOOL_NAME}\n"
        "Ollama did not yield a tool DataFrame (tool_choice should force this tool).\n"
        "Try: `ollama pull llama3.2` (or another tool-strong tag), set MODEL, "
        "upgrade Ollama, and re-run.\n"
        f"(Raw response type: {type(raw1).__name__}. Preview: {preview!r})\n"
    )

cohort_df = coerced_df

# Status: cohort from native tool_calls and/or JSON-shaped tool text in message.content (see LabHW2 functions.py)
print("--- Agent 1 status ---", flush=True)
print(f"  Tool registered for Agent 1: {AGENT1_TOOL_NAME}", flush=True)
print("  Ollama tool_choice: forced; Python runs the tool (native API or text-JSON recovery)", flush=True)
print("  Cohort DataFrame produced: yes", flush=True)
print(f"  Cohort rows: {len(cohort_df)}", flush=True)
print("----------------------", flush=True)

n_patients = (
    int(cohort_df["patient_id"].nunique()) if "patient_id" in cohort_df.columns else len(cohort_df)
)
agent1_md = "\n".join(
    [
        "# LabHW2 — Agent 1 cohort findings",
        "",
        "## Run metadata",
        "",
        f"- **Ollama model:** `{MODEL}`",
        f"- **Tool offered to the model:** `{AGENT1_TOOL_NAME}`",
        "- **Tool execution:** Yes (Ollama `tool_calls` and/or recovery from JSON printed in assistant text)",
        f"- **Database:** `{DB_PATH}`",
        "- **Cohort rule:** PHQ-9 score > 15 and `safety_concerns` = Y",
        "",
        "## Summary",
        "",
        f"- Qualifying visits: **{len(cohort_df)}**",
        f"- Unique patients (by `patient_id`): **{n_patients}**",
        "",
        "## Full cohort (all columns)",
        "",
        df_as_text(cohort_df),
        "",
    ]
)
OUT_AGENT1.write_text(agent1_md, encoding="utf-8")
print(f"Wrote Agent 1 hand-in file: {OUT_AGENT1}", flush=True)

print(
    "Calling Agent 2 (clinical synopsis) — with smollm2 this can take a few minutes…",
    flush=True,
)

summary_cols = [
    "patient_id",
    "patient_name",
    "visit_date",
    "phq9_score",
    "safety_concerns",
    "diagnosis",
    "provider",
]
cols_ok = [c for c in summary_cols if c in cohort_df.columns]
cohort_sl = cohort_df[cols_ok] if cols_ok else cohort_df
n_unique = cohort_df["patient_id"].nunique() if "patient_id" in cohort_df.columns else len(cohort_df)
cohort_table = df_as_text(cohort_sl)

role2 = (
    "You are a clinical chart reviewer writing for a quality committee. "
    "Use ONLY the data in the user message. If the table is empty, say so clearly. "
    "Do not fabricate patient identifiers or scores. Write in professional clinical prose."
)
task2 = (
    "Cohort: visits with PHQ-9 > 15 and safety_concerns = Y.\n"
    f"- Total qualifying visits: {len(cohort_df)}\n"
    f"- Unique patients (by patient_id): {n_unique}\n\n"
    "Markdown table (key columns only; medications omitted to save context):\n"
    f"{cohort_table}\n\n"
    "Produce a one-page synopsis in Markdown with these sections:\n"
    "## Cohort overview\n"
    "## Safety and symptom severity themes\n"
    "## Suggested follow-up (operational, non-prescriptive)\n"
    "Keep it concise (about one printed page). End with a short bullet list of "
    "data limitations (synthetic data, single-site context, etc.)."
)

synopsis_md = agent_run(role=role2, task=task2, model=MODEL, tools=None, output="text")

# 3. WRITE SYNOPSIS AND SHOW RESULTS ###################################

OUT_SYNOPSIS.write_text(synopsis_md, encoding="utf-8")

print("Agent 2 done.", flush=True)
print(cohort_df.head())
print()
print(f"Wrote Agent 2 hand-in file: {OUT_SYNOPSIS}")
print()
print("Agent 2 synopsis preview (first 1200 chars):")
print(synopsis_md[:1200])
if len(synopsis_md) > 1200:
    print("...")
