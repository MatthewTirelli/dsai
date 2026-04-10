# 02_ai_quality_control.py
# AI-Assisted Text Quality Control
# Tim Fraser

# This script demonstrates how to use AI (Ollama or OpenAI) to perform quality control
# on AI-generated text reports. It implements quality control criteria including
# boolean accuracy checks and Likert scales for multiple quality dimensions.
# Students learn to design quality control prompts and structure AI outputs as JSON.

# 0. Setup #################################

## 0.1 Load Packages #################################

# If you haven't already, install required packages:
# pip install pandas requests python-dotenv

import pandas as pd  # for data wrangling
import re  # for text processing
import requests  # for HTTP requests
import json  # for JSON operations
import os  # for environment variables
import time
from pathlib import Path

from dotenv import load_dotenv  # for loading .env file

## 0.2 Configuration #################################

# Choose your AI provider: "ollama" or "openai"
AI_PROVIDER = "ollama"  # Change to "openai" if using OpenAI

# Ollama configuration
PORT = 11434
OLLAMA_HOST = f"http://localhost:{PORT}"
OLLAMA_MODEL = "llama3.2:latest"  # Use a model that supports JSON output

# Set True to call the API twice per report (original + revised rubric) and save
# 09_text_analysis/data/qc_prompt_ab_scores.csv for 04_qc_rubric_comparison.py
# When True, the inline demo below is skipped to avoid duplicate API calls.
EXPORT_DUAL_QC_CSV = True

# OpenAI configuration
#load_dotenv()
#OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
#OPENAI_MODEL = "gpt-4o-mini"  # Low-cost model

## 0.3 Load Sample Data #################################

# Load sample report text for quality control
with open("09_text_analysis/data/sample_reports.txt", "r", encoding="utf-8") as f:
    sample_text = f.read()

# Split text into individual reports
reports = [r.strip() for r in sample_text.split("\n\n") if r.strip()]
report = reports[0]

# Load source data (if available) for accuracy checking
# In this example, we'll use a simple data structure
source_data = """White County, IL | 2015 | PM10 | Time Driven | hours
|type        |label_value |label_percent |
|:-----------|:-----------|:-------------|
|Light Truck |2.7 M       |51.8%         |
|Car/ Bike   |1.9 M       |36.1%         |
|Combo Truck |381.3 k     |7.3%          |
|Heavy Truck |220.7 k     |4.2%          |
|Bus         |30.6 k      |0.6%          |"""

QC_AB_CSV = Path("09_text_analysis/data/qc_prompt_ab_scores.csv")

print("📝 Report for Quality Control:")
print("---")
print(report)
print("---\n")

# 1. AI Quality Control Function #################################

## 1.1 Create Quality Control Prompts #################################
#
# Design note (homework): we keep TWO rubrics:
# - **original** — baseline criteria (short labels), same JSON shape as the lesson started with.
# - **revised** — tighter instructions for factuality + one extra Likert (**completeness**).
# Three *example* improvements you could discuss in a reflection:
# (1) Tie **accurate** / **accuracy** to numbers, rankings, and unsupported claims (not just "misinterprets").
# (2) Add **completeness** so the model checks coverage of the source table, not only tone.
# (3) Ask for JSON only and name keys explicitly (stricter contract, easier parsing).


def create_quality_control_prompt_original(report_text, source_data=None):
    """
    Baseline QC rubric (assignment starting point).
    """
    instructions = (
        "You are a quality control validator for AI-generated reports. "
        "Evaluate the following report text on multiple criteria and return your assessment as valid JSON."
    )

    data_context = ""
    if source_data is not None:
        data_context = f"\n\nSource Data:\n{source_data}\n"

    criteria = """

Quality Control Criteria:

1. **accurate** (boolean): Verify that no part of the paragraph misinterprets the data supplied. Return TRUE if no misinterpretation. FALSE if any problems.

2. **accuracy** (1-5 Likert scale): Rank the paragraph on a 5-point Likert scale, where 1 = many problems interpreting the Data vs. 5 = no misinterpretation of the Data.

3. **formality** (1-5 Likert scale): Rank the paragraph on a 5-point Likert scale, where 1 = casual writing vs. 5 = government report writing.

4. **faithfulness** (1-5 Likert scale): Rank the paragraph on a 5-point Likert scale, where 1 = makes grandiose claims not supported by the data vs. 5 = makes claims directly related to the data.

5. **clarity** (1-5 Likert scale): Rank the paragraph on a 5-point Likert scale, where 1 = confusing writing style vs. 5 = clear and precise.

6. **succinctness** (1-5 Likert scale): Rank the paragraph on a 5-point Likert scale, where 1 = unnecessarily wordy vs. 5 = succinct.

7. **relevance** (1-5 Likert scale): Rank the paragraph on a 5-point Likert scale, where 1 = irrelevant commentary vs. 5 = relevant commentary about the data.

Return your response as valid JSON in this exact format:
{
  "accurate": true/false,
  "accuracy": 1-5,
  "formality": 1-5,
  "faithfulness": 1-5,
  "clarity": 1-5,
  "succinctness": 1-5,
  "relevance": 1-5,
  "details": "0-50 word explanation of your assessment"
}
"""

    return f"{instructions}{data_context}\n\nReport Text to Validate:\n{report_text}{criteria}"


def create_quality_control_prompt_revised(report_text, source_data=None):
    """
    Revised rubric: sharper factuality checks + **completeness** Likert.
    (See module docstring / homework writeup for before-vs-after rationale.)
    """
    instructions = (
        "You are a quality control validator. Compare the report to the Source Data when provided. "
        "Return ONLY a single JSON object (no markdown fences, no extra text)."
    )

    data_context = ""
    if source_data is not None:
        data_context = f"\n\nSource Data:\n{source_data}\n"

    criteria = """

Quality Control Criteria (use integers 1-5 for Likert items):

1. **accurate** (boolean): TRUE only if ALL apply: (a) numeric values and percentages in the report match the Source Data (allow minor rounding); (b) relative rankings (e.g., which category is largest) match the Source Data; (c) there are no invented numbers or unsupported factual claims. Otherwise FALSE.

2. **accuracy** (1-5 Likert): 1 = multiple numerical, ranking, or exaggeration errors vs the Source Data; 3 = minor issues; 5 = fully consistent with the Source Data on numbers and ordering.

3. **formality** (1-5): 1 = casual; 5 = formal / report-like.

4. **faithfulness** (1-5): 1 = overstates differences or implies conclusions beyond the data; 5 = claims stay proportional to the evidence.

5. **clarity** (1-5): 1 = hard to follow; 5 = clear and precise.

6. **succinctness** (1-5): 1 = wordy; 5 = concise.

7. **relevance** (1-5): 1 = off-topic; 5 = focused on the data.

8. **completeness** (1-5): 1 = omits major categories or key breakdowns visible in the Source Data; 3 = mentions most; 5 = covers the main rows/categories without large gaps (if no Source Data, score based on internal consistency only).

Return JSON exactly in this shape (boolean lowercase, numbers as integers):
{
  "accurate": true,
  "accuracy": 3,
  "formality": 3,
  "faithfulness": 3,
  "clarity": 3,
  "succinctness": 3,
  "relevance": 3,
  "completeness": 3,
  "details": "short explanation citing numbers or gaps if relevant"
}
"""

    return f"{instructions}{data_context}\n\nReport Text to Validate:\n{report_text}{criteria}"


# Backward-compatible name used elsewhere in the course = baseline rubric
create_quality_control_prompt = create_quality_control_prompt_original

## 1.2 Query AI Function #################################

# Function to query AI and get quality control results
def query_ai_quality_control(prompt, provider=AI_PROVIDER):
    if provider == "ollama":
        # Query Ollama
        url = f"{OLLAMA_HOST}/api/chat"

        body = {
            "model": OLLAMA_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "format": "json",  # Request JSON output
            "stream": False
        }

        response = requests.post(url, json=body)
        response.raise_for_status()
        response_data = response.json()
        output = response_data["message"]["content"]

    elif provider == "openai":
        # Query OpenAI
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in .env file. Please set it up first.")

        url = "https://api.openai.com/v1/chat/completions"

        body = {
            "model": OPENAI_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a quality control validator. Always return your responses as valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "response_format": {"type": "json_object"},  # Request JSON output
            "temperature": 0.3  # Lower temperature for more consistent validation
        }

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        response_data = response.json()
        output = response_data["choices"][0]["message"]["content"]

    else:
        raise ValueError("Invalid provider. Use 'ollama' or 'openai'.")

    return output

## 1.3 Parse Quality Control Results #################################


def _extract_json_object(json_response):
    json_match = re.search(r"\{.*\}", json_response, re.DOTALL)
    if json_match:
        json_response = json_match.group(0)
    return json.loads(json_response)


def parse_quality_control_results(json_response, variant="original"):
    """
    Parse JSON from the model into one-row DataFrame.

    variant:
      - "original" — 6 Likert scales + accurate + details (no completeness).
      - "revised" — adds **completeness** Likert; overall_score uses 7 Likerts.
    """
    quality_data = _extract_json_object(json_response)

    base = {
        "accurate": [quality_data["accurate"]],
        "accuracy": [quality_data["accuracy"]],
        "formality": [quality_data["formality"]],
        "faithfulness": [quality_data["faithfulness"]],
        "clarity": [quality_data["clarity"]],
        "succinctness": [quality_data["succinctness"]],
        "relevance": [quality_data["relevance"]],
        "details": [quality_data.get("details", "")],
    }

    if variant == "original":
        base["completeness"] = [float("nan")]
        likert_cols = ["accuracy", "formality", "faithfulness", "clarity", "succinctness", "relevance"]
    else:
        base["completeness"] = [int(quality_data.get("completeness", 3))]
        likert_cols = [
            "accuracy",
            "formality",
            "faithfulness",
            "clarity",
            "succinctness",
            "relevance",
            "completeness",
        ]

    results = pd.DataFrame(base)
    shared = ["accuracy", "formality", "faithfulness", "clarity", "succinctness", "relevance"]
    results["overall_six"] = round(results[shared].astype(float).mean(axis=1), 2)
    overall = results[likert_cols].astype(float).mean(axis=1)
    results["overall_score"] = round(float(overall.iloc[0]), 2)
    return results


# 2. Run Quality Control #################################

## 2.1 Demo: both rubrics on the first report (skipped when exporting CSV) #################################

if not EXPORT_DUAL_QC_CSV:
    print("🤖 Querying AI — original rubric...\n")
    quality_prompt_orig = create_quality_control_prompt_original(report, source_data)
    ai_response_orig = query_ai_quality_control(quality_prompt_orig, provider=AI_PROVIDER)
    print("📥 AI Response (original, raw):")
    print(ai_response_orig)
    print()

    quality_results_orig = parse_quality_control_results(ai_response_orig, variant="original")
    print("✅ Quality Control Results (original):")
    print(quality_results_orig)
    print()

    print("🤖 Querying AI — revised rubric...\n")
    quality_prompt_rev = create_quality_control_prompt_revised(report, source_data)
    ai_response_rev = query_ai_quality_control(quality_prompt_rev, provider=AI_PROVIDER)
    print("📥 AI Response (revised, raw):")
    print(ai_response_rev)
    print()

    quality_results_rev = parse_quality_control_results(ai_response_rev, variant="revised")
    print("✅ Quality Control Results (revised):")
    print(quality_results_rev)
    print()

    print(
        f"📊 Original overall (6 Likerts): {quality_results_orig['overall_score'].values[0]:.2f} / 5.0"
    )
    print(
        f"📊 Revised overall (7 Likerts incl. completeness): {quality_results_rev['overall_score'].values[0]:.2f} / 5.0"
    )
    print(f"📊 Fair comparison mean (shared 6 Likerts, revised): {quality_results_rev['overall_six'].values[0]:.2f}")
    print(
        f"📊 Accuracy check (original): {'✅ PASS' if quality_results_orig['accurate'].values[0] else '❌ FAIL'}"
    )
    print(
        f"📊 Accuracy check (revised): {'✅ PASS' if quality_results_rev['accurate'].values[0] else '❌ FAIL'}\n"
    )


## 2.2 Export paired scores for statistical comparison (04_qc_rubric_comparison.py) #################################


def export_dual_prompt_scores_to_csv(
    report_list,
    source_data_str,
    csv_path: Path,
    provider=AI_PROVIDER,
    sleep_s: float = 1.0,
):
    """
    For each report, run original and revised QC and stack rows with columns:
    report_id, prompt_version, accurate, accuracy, ..., completeness, overall_score, details
    """
    rows = []
    for i, report_text in enumerate(report_list, start=1):
        print(f"📤 Export row pair {i}/{len(report_list)} (original + revised)...")
        for version, builder, variant in (
            ("original", create_quality_control_prompt_original, "original"),
            ("revised", create_quality_control_prompt_revised, "revised"),
        ):
            prompt = builder(report_text, source_data_str)
            try:
                raw = query_ai_quality_control(prompt, provider=provider)
                df = parse_quality_control_results(raw, variant=variant)
            except Exception as e:
                print(f"   ❌ {version} report {i}: {e}")
                continue
            df.insert(0, "prompt_version", version)
            df.insert(0, "report_id", i)
            rows.append(df)
            time.sleep(sleep_s)
    if not rows:
        print("⚠️ No rows to save.")
        return
    out = pd.concat(rows, ignore_index=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(csv_path, index=False)
    print(f"\n💾 Saved {len(out)} rows to {csv_path}")


if EXPORT_DUAL_QC_CSV:
    print("\n" + "=" * 60)
    print("Exporting dual-prompt QC scores for statistical comparison...")
    print("=" * 60 + "\n")
    export_dual_prompt_scores_to_csv(reports, source_data, QC_AB_CSV, provider=AI_PROVIDER)

# 3. Quality Control Multiple Reports (original rubric only) #################################

## 3.1 Batch Quality Control Function #################################


def check_multiple_reports(reports, source_data=None):
    print(f"🔄 Performing quality control on {len(reports)} reports...\n")

    all_results = []

    for i, report_text in enumerate(reports, 1):
        print(f"Checking report {i} of {len(reports)}...")

        # Create prompt
        prompt = create_quality_control_prompt_original(report_text, source_data)

        # Query AI
        try:
            response = query_ai_quality_control(prompt, provider=AI_PROVIDER)
            results = parse_quality_control_results(response, variant="original")
            results["report_id"] = i
            all_results.append(results)
        except Exception as e:
            print(f"❌ Error checking report {i}: {e}")

        time.sleep(1)

    # Combine all results
    if all_results:
        combined_results = pd.concat(all_results, ignore_index=True)
        return combined_results
    else:
        return pd.DataFrame()


## 3.2 Run Batch Quality Control (Optional) #################################

# Uncomment to check all reports
# if len(reports) > 1:
#     batch_results = check_multiple_reports(reports, source_data)
#     print("\n📊 Batch Quality Control Results:")
#     print(batch_results)

print("✅ AI quality control complete!")
print("💡 Compare these results with manual quality control (01_manual_quality_control.py) to see how AI performs.")
print(f"💡 For Bartlett / paired t-tests on original vs revised rubric, run 04_qc_rubric_comparison.py (reads {QC_AB_CSV}).")
