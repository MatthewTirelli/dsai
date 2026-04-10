# manual_qc_metrics.py
# Shared manual QC logic (mirrors 01_manual_quality_control.py)
# Tim Fraser

import re

import pandas as pd

REQUIRED_CONCEPTS = [
    "emissions",
    "county",
    "year",
    "pollutant",
    "recommendations",
    "data",
]


def compute_manual_metrics(text: str, report_id: int) -> dict[str, object]:
    """
    Return one row of manual QC features for a single report string.
    Same rules as 01_manual_quality_control.py (regex + keyword presence).
    """
    concept_present = [
        len(re.findall(re.escape(term), text, re.IGNORECASE)) > 0
        for term in REQUIRED_CONCEPTS
    ]
    words = text.split()
    word_count = len(words)
    sentence_count = len(re.findall(r"[.!?]+", text))
    avg_words = word_count / max(sentence_count, 1)

    has_numbers = bool(re.search(r"\d+", text))
    has_percentages = bool(re.search(r"\d+%", text))
    has_recommendations = bool(re.search(r"recommend|suggest|should|must", text, re.IGNORECASE))
    has_contractions = bool(re.search(r"'t|'s|'d|'ll|'ve|'re|'m", text, re.IGNORECASE))
    has_hyperbole = bool(re.search(r"crucial|critical|extremely|absolutely", text, re.IGNORECASE))
    has_belittling = bool(re.search(r"it is clear that|obviously|as you can see", text, re.IGNORECASE))

    concept_coverage = sum(concept_present) / len(concept_present)

    numbers = re.findall(r"\d+(?:\.\d+)?", text)
    number_count = len(numbers)
    percentage_count = len(re.findall(r"\d+%", text))

    return {
        "report_id": report_id,
        "word_count": word_count,
        "sentence_count": sentence_count,
        "avg_words_per_sentence": round(avg_words, 2),
        "has_numbers": has_numbers,
        "has_percentages": has_percentages,
        "has_recommendations": has_recommendations,
        "has_contractions": has_contractions,
        "has_hyperbole": has_hyperbole,
        "has_belittling": has_belittling,
        "concept_coverage": round(concept_coverage, 4),
        "number_count": number_count,
        "percentage_count": percentage_count,
    }


def manual_qc_all_reports(reports: list[str]) -> pd.DataFrame:
    """One row per report (id 1..n)."""
    rows = [compute_manual_metrics(reports[i], i + 1) for i in range(len(reports))]
    return pd.DataFrame(rows)
