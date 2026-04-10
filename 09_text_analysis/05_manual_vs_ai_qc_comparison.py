# 05_manual_vs_ai_qc_comparison.py
# Compare manual QC (01-style regex/keywords) with AI QC scores (02 export)
#
# Manual and AI metrics are NOT on the same scale — this script joins them by report_id
# so you can inspect patterns (e.g. concept_coverage vs AI relevance; has_hyperbole vs faithfulness).
#
# Run from repo root:
#   python3 09_text_analysis/05_manual_vs_ai_qc_comparison.py
#
# Needs: 09_text_analysis/data/sample_reports.txt
# Optional: 09_text_analysis/data/qc_prompt_ab_scores.csv (from 02 with EXPORT_DUAL_QC_CSV = True)

from pathlib import Path

import pandas as pd

from manual_qc_metrics import manual_qc_all_reports

ROOT = Path("09_text_analysis/data")
SAMPLE_REPORTS = ROOT / "sample_reports.txt"
AI_SCORES = ROOT / "qc_prompt_ab_scores.csv"
OUT_CSV = ROOT / "manual_vs_ai_qc_merged.csv"


def main() -> None:
    print("=" * 72)
    print(" MANUAL vs AI QC — what this comparison can and cannot do")
    print("=" * 72)
    print(
        """
**Manual QC (01)** uses fixed rules: keyword presence, regex for numbers/percentages,
style flags (hyperbole, belittling), and **concept_coverage** (share of required terms found).

**AI QC (02)** asks a model for Likert ratings (accuracy, formality, …) vs **Source Data**
in the prompt — semantic judgment, not the same checklist.

So you should **not** expect one manual number to “equal” one AI number. Good uses:
  • Side-by-side tables per report_id (same text, three views: manual + original rubric + revised).
  • Hypotheses like “reports with higher **concept_coverage** tend to get higher AI **relevance**”
    (exploratory correlation — needs enough reports).
"""
    )

    if not SAMPLE_REPORTS.is_file():
        print(f"❌ Missing {SAMPLE_REPORTS}")
        return

    sample_text = SAMPLE_REPORTS.read_text(encoding="utf-8")
    reports = [r.strip() for r in sample_text.split("\n\n") if r.strip()]
    manual_df = manual_qc_all_reports(reports)
    manual_df = manual_df.add_prefix("manual_").rename(columns={"manual_report_id": "report_id"})

    print("\n--- Manual QC features (all reports) ---\n")
    print(manual_df.to_string(index=False))
    print()

    if not AI_SCORES.is_file():
        print(f"⚠️ No {AI_SCORES} — run 02_ai_quality_control.py with EXPORT_DUAL_QC_CSV = True first.")
        print("   Saving manual-only table.\n")
        manual_df.to_csv(OUT_CSV, index=False)
        print(f"💾 Wrote {OUT_CSV}")
        return

    ai = pd.read_csv(AI_SCORES)
    # Long format: report_id × prompt_version; merge manual once per report
    ai = ai.rename(
        columns={
            c: f"ai_{c}"
            for c in ai.columns
            if c not in ("report_id", "prompt_version")
        }
    )

    merged = ai.merge(manual_df, on="report_id", how="left")

    print("--- Merged: manual features + AI scores (one row per report × AI rubric) ---\n")
    # Show key columns only for readability
    show_cols = [
        "report_id",
        "prompt_version",
        "manual_concept_coverage",
        "manual_has_hyperbole",
        "manual_number_count",
        "ai_overall_six",
        "ai_accuracy",
        "ai_relevance",
    ]
    show_cols = [c for c in show_cols if c in merged.columns]
    print(merged[show_cols].to_string(index=False))
    print("\n(Full merge includes all manual_* and ai_* columns.)\n")

    merged.to_csv(OUT_CSV, index=False)
    print(f"💾 Wrote full merge to {OUT_CSV}")

    # Exploratory correlation: revised rubric only, numeric
    rev = merged[merged["prompt_version"] == "revised"].copy()
    if len(rev) >= 3:
        try:
            r = rev["manual_concept_coverage"].astype(float).corr(
                rev["ai_overall_six"].astype(float)
            )
            print(
                f"\n📎 Exploratory Pearson r (manual concept_coverage vs AI overall_six, revised only): {r:.3f}"
            )
            print("   (Interpret cautiously: small n, different constructs.)\n")
        except Exception:
            pass

    print("✅ Done.")


if __name__ == "__main__":
    main()
