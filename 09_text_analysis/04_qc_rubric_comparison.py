# 04_qc_rubric_comparison.py
# Compare original vs revised QC rubric scores (paired reports)
# Tim Fraser / course extension
#
# Input: 09_text_analysis/data/qc_prompt_ab_scores.csv
#   (generate with 02_ai_quality_control.py and EXPORT_DUAL_QC_CSV = True)
#
# Run from repo root:
#   python3 09_text_analysis/04_qc_rubric_comparison.py

from pathlib import Path
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.stats import bartlett
import pingouin as pg

QC_AB_PATH = Path("09_text_analysis/data/qc_prompt_ab_scores.csv")

# Human-readable labels (what “original” and “revised” mean in this pipeline)
LABEL_ORIGINAL = "Original QC rubric (baseline lesson prompt)"
LABEL_REVISED = "Revised QC rubric (stricter factuality + completeness)"


def _pingouin_col(df, *names):
    """Pingouin renamed hyphenated column names to underscores in newer versions."""
    for n in names:
        if n in df.columns:
            return df[n].values[0]
    raise KeyError(f"Expected one of {names}; columns={list(df.columns)}")


def _conclusion_text(mean_diff: float, p_t: float, dim: str) -> str:
    """Plain-language takeaway for paired comparison (Revised minus Original)."""
    if np.isnan(p_t):
        return (
            "We cannot run a paired t-test here (e.g. every report got the same score under both rubrics). "
            "There is no variation in paired differences to test."
        )
    if p_t >= 0.05:
        return (
            f"No statistically significant shift between rubrics on **{dim}** (paired p = {p_t:.4f}). "
            "Any mean gap you see could plausibly be random noise at usual α = 0.05."
        )
    if mean_diff > 0:
        return (
            "The **revised** scoring rubric gave **significantly higher** mean scores than the **original** rubric "
            f"on **{dim}** (paired p = {p_t:.4f}). On this scale, a higher number is a stronger/better rating."
        )
    if mean_diff < 0:
        return (
            "The **original** scoring rubric gave **significantly higher** mean scores than the **revised** rubric "
            f"on **{dim}** (paired p = {p_t:.4f}). "
            "So the revised rubric produced lower average scores on this criterion for these reports."
        )
    return f"Paired p = {p_t:.4f}, but the mean difference is effectively zero."


def main() -> None:
    if not QC_AB_PATH.is_file():
        print(f"❌ File not found: {QC_AB_PATH}")
        print(
            "   Generate it: set EXPORT_DUAL_QC_CSV = True in 02_ai_quality_control.py, "
            "then run that script from the repo root."
        )
        sys.exit(1)

    ab = pd.read_csv(QC_AB_PATH)

    print("=" * 72)
    print(" QC RUBRIC COMPARISON — what this script does")
    print("=" * 72)
    print(
        "Each row in your CSV is one report scored with ONE scoring prompt.\n"
        f"  • {LABEL_ORIGINAL}\n"
        f"  • {LABEL_REVISED}\n"
        "\n"
        "The **same** report text is evaluated twice (paired). We report, for each numeric criterion:\n"
        "  1. Scores under each rubric (per report, then mean & standard deviation)\n"
        "  2. Bartlett’s test — checks whether spread (variance) differs between the two rubrics’ scores\n"
        "  3. Paired t-test — tests whether **mean** scores differ between the two rubrics on the same reports\n"
        "  4. A short conclusion in everyday language\n"
    )
    print(f"Data file: {QC_AB_PATH.resolve()}")
    print(f"Total rows in file: {len(ab)}")
    print("=" * 72 + "\n")

    if ab["accurate"].dtype == object:
        ab["accurate"] = ab["accurate"].map(lambda x: str(x).lower() in ("true", "1", "yes"))

    orig = ab[ab["prompt_version"] == "original"].sort_values("report_id").reset_index(drop=True)
    rev = ab[ab["prompt_version"] == "revised"].sort_values("report_id").reset_index(drop=True)

    if len(orig) == 0 or len(rev) == 0:
        print("⚠️ Need both prompt_version == 'original' and 'revised' rows.")
        sys.exit(1)

    if len(orig) != len(rev) or not orig["report_id"].equals(rev["report_id"]):
        print("⚠️ original/revised rows do not align by report_id; check the CSV.")
        sys.exit(1)

    n = len(orig)
    print(f"Number of paired reports: {n}\n")

    # Overview table
    print("-" * 72)
    print("OVERVIEW — mean of each numeric column by rubric")
    print("-" * 72)
    num_cols = [
        c
        for c in ab.columns
        if c not in ("report_id", "prompt_version", "details")
        and pd.api.types.is_numeric_dtype(ab[c])
    ]
    desc = ab.groupby("prompt_version")[num_cols].agg(["mean", "std"]).round(3)
    print(desc)
    print()

    paired_dims = [
        "accuracy",
        "formality",
        "faithfulness",
        "clarity",
        "succinctness",
        "relevance",
        "overall_six",
        "overall_score",
    ]

    print(
        "Note: **overall_score** = mean of 6 Likerts (original) vs 7 (revised, includes completeness). "
        "**overall_six** = mean of the **same six** Likerts for both — best for apples-to-apples.\n"
    )
    print(
        "Caution: with very few reports, Likert scores often repeat → variance can be zero → "
        "Bartlett may be unreliable or nan; conclusions lean on means and common sense.\n"
    )

    for dim in paired_dims:
        if dim not in orig.columns:
            continue

        x = orig[dim].astype(float).values
        y = rev[dim].astype(float).values
        mean_diff = float(np.mean(y - x))
        diffs = y - x

        mo, so = float(np.mean(x)), float(np.std(x, ddof=1)) if n > 1 else 0.0
        mr, sr = float(np.mean(y)), float(np.std(y, ddof=1)) if n > 1 else 0.0

        print("=" * 72)
        print(f" MEASURE: {dim}")
        print("=" * 72)

        print("\nPer-report scores (same report_id = same text, two different scoring prompts):\n")
        print(f"{'report_id':>10}  {'Original':>12}  {'Revised':>12}  {'Revised − Original':>18}")
        for i in range(n):
            rid = int(orig["report_id"].iloc[i])
            print(f"{rid:>10}  {x[i]:>12.3f}  {y[i]:>12.3f}  {diffs[i]:>+18.3f}")

        print("\n--- Summary statistics ---\n")
        print(f"  {LABEL_ORIGINAL}")
        print(f"      Mean = {mo:.4f}    Std dev = {so:.4f}    (n = {n} reports)\n")
        print(f"  {LABEL_REVISED}")
        print(f"      Mean = {mr:.4f}    Std dev = {sr:.4f}    (n = {n} reports)\n")
        print(f"  Mean of (Revised − Original) across reports: {mean_diff:+.4f}")

        # Bartlett
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            try:
                b_stat, b_p = bartlett(x, y)
                b_p = float(b_p)
            except Exception:
                b_stat, b_p = float("nan"), float("nan")

        print("\n--- Bartlett test (are the two rubrics’ score spreads different?) ---\n")
        if not np.isnan(b_p) and not np.isinf(b_stat):
            print(f"  Test statistic: {b_stat:.6f}")
            print(f"  p-value: {b_p:.6f}")
            if b_p < 0.05:
                print(
                    "  Meaning: variances differ significantly across rubrics (α = 0.05). "
                    "Interpret other tests with that in mind."
                )
            else:
                print(
                    "  Meaning: we do **not** reject equal spread at α = 0.05 (often a loose check with small n)."
                )
        else:
            print(
                "  Bartlett is not reliable here (non-finite statistic or nan p-value — typical when one rubric’s "
                "scores have zero spread, e.g. all the same Likert value). Do not use this p-value to draw conclusions."
            )

        # Paired t
        print("\n--- Paired t-test (do mean scores differ between rubrics on the same reports?) ---\n")
        p_t = float("nan")
        t_val = float("nan")
        dof = float("nan")
        if np.allclose(diffs, 0.0):
            print("  Not run: Revised and Original scores are **identical** for every report on this measure.")
            print("  (No variation in paired differences → t-test is not defined.)\n")
        else:
            try:
                tt = pg.ttest(x, y, paired=True)
                p_t = float(_pingouin_col(tt, "p-val", "p_val"))
                t_val = float(tt["T"].values[0])
                dof = float(tt["dof"].values[0])
                print(f"  t statistic: {t_val:.6f}")
                print(f"  degrees of freedom: {dof:.1f}")
                print(f"  two-sided p-value: {p_t:.6f}\n")
                print("  Full Pingouin table:")
                print(tt.to_string(index=False))
                print()
            except Exception as exc:
                print(f"  Could not compute paired t-test: {exc}\n")

        print("--- What to say in plain language ---\n")
        print(f"  {_conclusion_text(mean_diff, p_t, dim)}\n")

    if "completeness" in rev.columns and rev["completeness"].notna().any():
        print("=" * 72)
        print(" EXTRA: completeness (only defined for the revised rubric)")
        print("=" * 72)
        print(
            f"  Mean completeness score under the revised rubric: {rev['completeness'].mean():.4f}\n"
            "  (There is no separate ‘completeness’ column for the original rubric.)\n"
        )

    print("=" * 72)
    print(" Done.")
    print("=" * 72)


if __name__ == "__main__":
    main()
