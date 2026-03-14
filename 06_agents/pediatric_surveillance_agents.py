# pediatric_surveillance_agents.py
# Multi-Agent Pediatric Suicide Surveillance Workflow
# Three-agent pipeline: Data Context → Public Health Sentinel → Policy Advisor.
# Pairs with HW1 data source (CDC Socrata pediatric suicide).

# This script loads pediatric suicide surveillance data, then runs three LLM
# agents in sequence to contextualize the dataset, detect sentinel signals,
# and produce policy recommendations.

# 0. SETUP ###################################

## 0.1 Load packages and env #################################

import os
from pathlib import Path

# Load .env from project root so SOCRATA_APP_TOKEN is available
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
from dotenv import load_dotenv
load_dotenv(dotenv_path=_PROJECT_ROOT / ".env")

os.chdir(Path(__file__).resolve().parent)

from functions import (
    get_pediatric_suicide_df,
    agent_run,
    df_as_text,
)
import pandas as pd

MODEL = "gemma3"

# 1. LOAD DATA ###################################

# Dataset: pediatric suicide deaths (age < 15), by year and injury mechanism.
# No geographic/sex/age breakdown in this API pull; extend data source for those.
df = get_pediatric_suicide_df(limit=2000)

# 2. BUILD DATASET CONTEXT FOR AGENT 1 ###################################

# Summarize structure and content so the Data Context Agent can describe it.
def dataset_context_text(df):
    """Produce a text summary of the DataFrame for the Data Context Agent."""
    lines = []
    lines.append("COLUMN NAMES AND DTypes:")
    lines.append(df.dtypes.to_string())
    lines.append("\nNUMBER OF ROWS: " + str(len(df)))
    if "year" in df.columns:
        lines.append("YEARS COVERED: " + str(sorted(df["year"].unique().tolist())))
    if "injury_mechanism" in df.columns:
        lines.append("NUMBER OF UNIQUE INJURY MECHANISMS: " + str(df["injury_mechanism"].nunique()))
    lines.append("\nMISSING VALUES PER COLUMN:")
    lines.append(df.isnull().sum().to_string())
    lines.append("\nSAMPLE ROWS (first 15):")
    lines.append(df.head(15).to_markdown(index=False))
    lines.append("\nDESCRIPTIVE STATISTICS (numeric):")
    lines.append(df.describe().to_markdown())
    return "\n".join(lines)

task1 = dataset_context_text(df)

# 3. AGENT 1 — DATA CONTEXT AGENT ###################################

role1 = (
    "You are Agent 1 — Data Context Agent. Your role is to understand the dataset "
    "structure and produce a contextual summary for downstream analysis.\n\n"
    "Use ONLY the following dataset summary. Do not perform statistical analysis; "
    "only contextualize the dataset.\n\n"
    "Produce a structured summary with these sections:\n"
    "DATASET OVERVIEW\n"
    "VARIABLES IDENTIFIED\n"
    "DATA QUALITY ISSUES\n"
    "RECOMMENDED VARIABLES FOR ANALYSIS\n\n"
    "Note: This dataset may contain only year, injury_mechanism, and total_deaths "
    "(no geographic region, sex, or age group in this pull). Describe what is present."
)

summary1 = agent_run(role=role1, task=task1, model=MODEL, output="text")

# 4. PREPARE METRICS FOR AGENT 2 ###################################

# Compute surveillance metrics so the Sentinel Agent can interpret them.
by_year = df.groupby("year", as_index=False).agg(total_deaths=("total_deaths", "sum"))
by_mechanism = (
    df.groupby("injury_mechanism", as_index=False)
    .agg(total_deaths=("total_deaths", "sum"))
    .sort_values("total_deaths", ascending=False)
)

metrics_text = (
    "DEATHS BY YEAR:\n"
    + by_year.to_markdown(index=False)
    + "\n\nDEATHS BY INJURY MECHANISM (all years):\n"
    + by_mechanism.head(20).to_markdown(index=False)
)

task2_input = (
    "Below is the Data Context Agent's summary of the dataset.\n\n"
    "--- AGENT 1 SUMMARY ---\n"
    + summary1
    + "\n\n--- SURVEILLANCE METRICS (computed) ---\n"
    + metrics_text
)

# 5. AGENT 2 — PUBLIC HEALTH SENTINEL AGENT ###################################

role2 = (
    "You are Agent 2 — Public Health Sentinel Agent. Your role is to detect "
    "patterns, trends, and clusters indicating potential public health concerns.\n\n"
    "Using the dataset summary and the surveillance metrics provided, produce "
    "a structured report with these sections:\n"
    "KEY METRICS\n"
    "TEMPORAL TRENDS\n"
    "GEOGRAPHIC CLUSTERS (if data permits; otherwise note 'No geographic data in this dataset')\n"
    "HIGH-RISK GROUPS\n"
    "SENTINEL WARNINGS\n\n"
    "Focus on identifying meaningful signals that could warrant public health attention."
)

sentinel_output = agent_run(role=role2, task=task2_input, model=MODEL, output="text")

# 6. AGENT 3 — PUBLIC HEALTH POLICY ADVISOR ###################################

task3_input = (
    "Below are the Data Context summary and the Sentinel Agent's analysis.\n\n"
    "--- AGENT 1 (DATA CONTEXT) ---\n"
    + summary1
    + "\n\n--- AGENT 2 (SENTINEL) ---\n"
    + sentinel_output
)

role3 = (
    "You are Agent 3 — Public Health Policy Advisor. Your role is to interpret "
    "surveillance findings and recommend public health responses.\n\n"
    "Using the dataset summary and sentinel analysis provided, produce a structured "
    "report with these sections:\n"
    "SUMMARY OF FINDINGS\n"
    "AREAS OF CONCERN\n"
    "LIKELY PUBLIC HEALTH DRIVERS\n"
    "RECOMMENDED INTERVENTIONS\n"
    "PRIORITY ACTIONS FOR POLICYMAKERS\n\n"
    "Recommendations should be practical, actionable, and consistent with "
    "established public health practices."
)

policy_output = agent_run(role=role3, task=task3_input, model=MODEL, output="text")

# 7. VIEW RESULTS ###################################

print("\n" + "=" * 60)
print("AGENT 1 — DATA CONTEXT AGENT")
print("=" * 60)
print(summary1)

print("\n" + "=" * 60)
print("AGENT 2 — PUBLIC HEALTH SENTINEL AGENT")
print("=" * 60)
print(sentinel_output)

print("\n" + "=" * 60)
print("AGENT 3 — PUBLIC HEALTH POLICY ADVISOR")
print("=" * 60)
print(policy_output)
