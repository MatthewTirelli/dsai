# build_lab_submission_pdf.py
# Build LAB submission PDF: labeled code + console output, margins + wrapped lines.
# Run from repo: python 07_rag/build_lab_submission_pdf.py
# Or: cd 07_rag && python build_lab_submission_pdf.py

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    PageBreak,
    SimpleDocTemplate,
    Spacer,
)

# Optional: set your name before building (appears on cover line)
STUDENT_NAME = ""  # e.g. "Jane Doe"

# --- layout: avoid cutoff (letter, generous margins, wrapped monospace) ---

# ~0.85" margins -> content width ~6.8"; Courier 7pt ~ 86 chars/line at this width
LEFT_RIGHT = 0.85 * inch
TOP_BOTTOM = 0.75 * inch
MAX_CODE_CHARS = 86


def wrap_fixed_width(text: str, width: int = MAX_CODE_CHARS) -> str:
    """Hard-wrap long lines so PDF never clips horizontally."""
    out_lines: list[str] = []
    for raw in text.splitlines():
        line = raw
        if not line:
            out_lines.append("")
            continue
        while len(line) > width:
            out_lines.append(line[:width])
            line = line[width:]
        out_lines.append(line)
    return "\n".join(out_lines)


def escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def code_block_paragraphs(text: str, style: ParagraphStyle, lines_per_chunk: int = 42) -> list:
    """
    Render monospace code as wrapped Paragraph chunks so long files render reliably
    (ReportLab handles many small Paragraphs better than one huge block).
    """
    wrapped = wrap_fixed_width(text)
    lines = wrapped.splitlines()
    chunks: list = []
    for i in range(0, len(lines), lines_per_chunk):
        block = lines[i : i + lines_per_chunk]
        body = "<br/>".join(escape_xml(line) for line in block)
        chunks.append(Paragraph(body, style))
        chunks.append(Spacer(1, 3))
    return chunks


# Console output from latest run (demo mode); update if you re-run 06_patients_rag.py
CONSOLE_OUTPUT = r"""
============================================================
Q1: How many distinct patients does a given provider have?
    (demo provider: Dr. Aguilar)
SQL retrieval: [{'distinct_patient_count': 2}]
This provider is associated with two distinct patients based on the available records.

*   Distinct Patient Count: 2

============================================================
Q2: Synopsis of care for one patient
    (demo patient_id: 1)
**Patient Synopsis: Justin Miller**

*   **Initial Assessment:** Mr. Miller's care began with a diagnosis of Panic Disorder (visit ID 1) with an associated PHQ-9 score of 4 and medication of Adderall prescribed by Dr. Smith.
*   **Anxiety and Depression:** Subsequent visits (visit IDs 2, 3, 4, and 5) revealed a fluctuating presentation. Initially, Generalized Anxiety Disorder was diagnosed (visit ID 2) with a PHQ-9 score of 8 and Mirtazapine prescribed by Dr. Pierce.  A diagnosis of Persistent Depressive Disorder was later established (visits ID 3 and 4) with PHQ-9 scores of 5 and 6, respectively, and treatment with Escitalopram, Vyvanse, Venlafaxine, and Mirtazapine prescribed by Dr. Hutchinson and Dr. Campbell.
*   **Current Diagnosis:** At the last recorded visit (visit ID 5), a diagnosis of Major Depressive Disorder was noted with a PHQ-9 score of 6 and medications of Lamotrigine, Vyvanse, and Mirtazapine prescribed by Dr. Collier.

No visits were recorded prior to February 27, 2026.

============================================================
Q3: High-risk visits (PHQ-9 > 15) — synopsis of this cohort
    (rows retrieved: 135)
Here's a summary of the provided search data:

*   **Total Records:** 135
*   **Patient Data:** The records include information for 83 unique patients.

**Patient Diagnoses and PHQ9 Scores:**

*   **ADHD:** Kevin Holmes (51) appears in 3 records with a PHQ9 score of 27, 23, and 22. Scott Meyer (17) appears in 2 records with a PHQ9 score of 20 and 16.
*   **Generalized Anxiety Disorder:** Max Wilson (2) appears in 1 record with a PHQ9 score of 27. Daniel Smith (75) appears in 2 records with a PHQ9 score of 25 and 21.
*   **Social Anxiety Disorder:** Kevin Holmes (51) appears in 3 records with a PHQ9 score of 27, 22, and 16. Sharon Ramsey (46) appears in 4 records with a PHQ9 score of 22, 22, 17 and 16.
*   **Bipolar II Disorder:** Robert Hutchinson (37) appears in 3 records with a PHQ9 score of 26, 22, and 16. Amber Ferguson (47) appears in 2 records with a PHQ9 score of 22 and 16.
*   **Persistent Depressive Disorder:** Danielle Ward (24) appears in 1 record with a PHQ9 score of 26.
*   **Obsessive-Compulsive Disorder:** Kevin Diaz (4) appears in 3 records with a PHQ9 score of 24, 22, and 16. Christian Cole (32) appears in 1 record with a PHQ9 score of 20.
*   **Panic Disorder:** Max Wilson (2) appears in 1 record with a PHQ9 score of 27. John Molina (71) appears in 2 records with a PHQ9 score of 21 and 16.
*   **PTSD:** Robert Hutchinson (37) appears in 1 record with a PHQ9 score of 25. Natasha Anderson (65) appears in 2 records with a PHQ9 score of 22 and 16.
*   **Major Depressive Disorder:** Tammy Williamson (54) appears in 2 records with a PHQ9 score of 25 and 17. Morgan Livingston (14) appears in 1 record with a PHQ9 score of 20.
*   **Specific Scores:** Several individuals have a PHQ9 score of 23.

**Providers:**

*   The records involve the following providers: Dr. Fuller, Dr. Brooks, Dr. Mitchell, Dr. Sims, Dr. Aguilar, Dr. Little, Dr. Rivas, Dr. Mcgrath, Dr. Nguyen, Dr. Black, Dr. Mckee, Dr. Arnold, Dr. Patel, Dr. Yu, Dr. Perez, Dr. Hardin, Dr. Garcia, Dr. Murphy, Dr. Olsen, Dr. Gomez, Dr. Stewart, Dr. Green, Dr. Watson, Dr. Lee, Dr. Rogers, Dr. Hall, Dr. Hudson, Dr. Miller, Dr. Ramirez, Dr. Carter, Dr. Wright, Dr. Freeman, Dr. Stone, Dr. Berry, Dr. Valenzuela, Dr. Jacobs, Dr. Rodgers, Dr. Chen, etc.

============================================================
Q4: Patients not seen in over 60 days (since last visit)
    (rows retrieved: 69)
    cohort aggregates (in JSON to LLM): mean_days=240.3, median_days=209.0, same_last_provider_all=False
## Overdue Follow-Up Summary

This summary identifies patients with overdue follow-up appointments based on the provided retrieval data.

*   **Patient Count:** 69 patients have an overdue follow-up appointment.
*   **Notable Patients:**
    *   Mark Mendoza (Patient ID: 91) was last seen on 2024-07-06.
    *   Wendy Jackson (Patient ID: 27) was last seen on 2024-07-23.
    *   Valerie Murphy (Patient ID: 48) was last seen on 2024-08-26.
    *   Charles Cross (Patient ID: 79) was last seen on 2024-09-24.
    *   Morgan Livingston (Patient ID: 14) was last seen on 2024-10-16.
    *   Jon Holland (Patient ID: 80) was last seen on 2024-12-07.
    *   Sarah Duran (Patient ID: 21) was last seen on 2025-01-20.
    *   Kathryn Johnson (Patient ID: 82) was last seen on 2025-02-17.
    *   Gilbert Roberts (Patient ID: 25) was last seen on 2025-02-28.
    *   Emily Price (Patient ID: 39) was last seen on 2025-03-11.
    *   William Riley (Patient ID: 100) was last seen on 2025-03-15.
    *   Krista Wilcox (Patient ID: 9) was last seen on 2025-03-16.
    *   Justin Hall (Patient ID: 89) was last seen on 2025-03-19.
    *   Laurie Chavez (Patient ID: 93) was last seen on 2025-03-21.
    *   Jerry Morris (Patient ID: 13) was last seen on 2025-04-03.
    *   Paul Murphy (Patient ID: 72) was last seen on 2025-04-08.
    *   Christian Cole (Patient ID: 32) was last seen on 2025-04-19.
    *   Gregory Robertson (Patient ID: 16) was last seen on 2025-05-22.
    *   Stephanie Ross (Patient ID: 62) was last seen on 2025-06-03.
    *   Katherine Edwards (Patient ID: 64) was last seen on 2025-06-23.
    *   Joseph Robertson (Patient ID: 78) was last seen on 2025-06-26.
    *   Maria Ramos (Patient ID: 74) was last seen on 2025-06-23.
    *   Douglas Mckenzie (Patient ID: 33) was last seen on 2025-06-26.
    *   Kyle Berger (Patient ID: 78) was last seen on 2025-06-26.
    *   Stephanie Dominguez (Patient ID: 94) was last seen on 2025-06-27.
    *   Scott Meyer (Patient ID: 17) was last seen on 2025-07-01.
    *   Marie Jensen (Patient ID: 76) was last seen on 2025-07-14.
    *   Diana Hall (Patient ID: 20) was last seen on 2025-07-16.
    *   Max Wilson (Patient ID: 2) was last seen on 2025-07-27.
    *   Gina Schwartz (Patient ID: 70) was last seen on 2025-07-31.
    *   Joshua Johnson (Patient ID: 55) was last seen on 2025-08-10.
    *   Rachel Nelson (Patient ID: 6) was last seen on 2025-08-10.
    *   Kevin Kim (Patient ID: 51) was last seen on 2025-08-10.
    *   Nicole Clay (Patient ID: 43) was last seen on 2025-08-25.
    *   Bronwyn Howard (Patient ID: 53) was last seen on 2025-08-28.
    *   Alicia Ross (Patient ID: 68) was last seen on 2025-09-04.
    *   Dominic Koch (Patient ID: 87) was last seen on 2025-09-26.
    *   Thomas Cardenas (Patient ID: 83) was last seen on 2025-09-27.
    *   Lauren Barrett (Patient ID: 63) was last seen on 2025-09-28.
    *   David Long (Patient ID: 15) was last seen on 2025-09-04.
    *   Ashley Bass (Patient ID: 23) was last seen on 2025-09-05.
    *   Jordan Carter (Patient ID: 71) was last seen on 2025-09-06.
    *   Harry Taylor (Patient ID: 50) was last seen on 2025-09-08.
    *   Dr. Harry Taylor (Patient ID: 50) was last seen on 2025-09-08.
    *   Sean Bell (Patient ID: 51) was last seen on 2025-09-08.
    *   Eric White (Patient ID: 56) was last seen on 2025-09-08.
    *   Richard Mcknight (Patient ID: 3) was last seen on 2025-09-26.

*   **Diagnosis Distribution:**
    *   Social Anxiety Disorder: 9 patients
    *   ADHD: 9 patients
    *   Bipolar II Disorder: 9 patients
    *   Major Depressive Disorder: 8 patients
    *   Panic Disorder: 8 patients
    *   Persistent Depressive Disorder: 6 patients
    *   Obsessive-Compulsive Disorder: 5 patients
    *   PTSD: 4 patients
    *   Generalized Anxiety Disorder: 11 patients

*   **Days Since Last Visit:**
    *   Mean days since last visit: 240.3 days
    *   Median days since last visit: 209 days

*   **Last Visit Providers:**
    *   Dr. Davis: 3 patients
    *   Dr. Bell: 2 patients
    *   Dr. Murphy: 1 patient
    *   Dr. Simmons: 1 patient
    *   Dr. Brown: 1 patient

**Note:** The mean and median days since last visit summarize the average time since the patient's last documented appointment. This data does not represent missed appointments.
""".strip()


BRIEF_EXPLANATION = """
<b>Data source:</b> Synthetic SQLite database <i>patients.db</i> (generated with <i>fakerdata.py</i>)
containing <i>patients</i> and <i>visits</i> tables with PHQ-9 scores, diagnoses, providers, and medications.
<br/><br/>
<b>Search / retrieval:</b> Parameterized SQL queries return exact rows or aggregates (counts, filters by PHQ-9
threshold and days since last visit). For the lapsed-follow-up query, cohort summary statistics are computed in
Python and included in the JSON. Results are passed to the local LLM (Ollama).
<br/><br/>
<b>System prompt:</b> Rules in <i>clinical_rag_rules.yaml</i> (loaded into the system message) require a
clinical, professional tone and prohibit inventing facts not present in the retrieval payload.
""".strip()


def build_pdf(out_path: Path, rag_dir: Path) -> None:
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Title"],
        fontSize=16,
        spaceAfter=14,
        alignment=TA_LEFT,
    )
    h1 = ParagraphStyle(
        "H1Custom",
        parent=styles["Heading1"],
        fontSize=13,
        spaceBefore=12,
        spaceAfter=8,
        textColor=colors.HexColor("#1a1a1a"),
        alignment=TA_LEFT,
    )
    h2 = ParagraphStyle(
        "H2Custom",
        parent=styles["Heading2"],
        fontSize=11,
        spaceBefore=10,
        spaceAfter=6,
        alignment=TA_LEFT,
    )
    body = ParagraphStyle(
        "BodyCustom",
        parent=styles["Normal"],
        fontSize=9,
        leading=11,
        alignment=TA_LEFT,
    )
    code_style = ParagraphStyle(
        "CodeBlock",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=7,
        leading=8.5,
        leftIndent=8,
        rightIndent=8,
        spaceBefore=4,
        spaceAfter=6,
        backColor=colors.HexColor("#f5f5f5"),
        borderColor=colors.grey,
        borderWidth=0.5,
        borderPadding=6,
        alignment=TA_LEFT,
    )

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=letter,
        leftMargin=LEFT_RIGHT,
        rightMargin=LEFT_RIGHT,
        topMargin=TOP_BOTTOM,
        bottomMargin=TOP_BOTTOM,
        title="LAB — Custom RAG Query (Patients)",
    )

    story: list = []

    story.append(Paragraph("LAB: Create Your Own RAG AI Query", title_style))
    name_line = (
        f"<b>Student:</b> {STUDENT_NAME}<br/>"
        if STUDENT_NAME.strip()
        else ""
    )
    story.append(
        Paragraph(
            name_line
            + "<b>Course / project:</b> SYSEN AIDATA (dsai) &nbsp;|&nbsp; "
            "<b>Folder:</b> 07_rag &nbsp;|&nbsp; <b>Submission files:</b> "
            "<i>clinical_rag_rules.yaml</i>, <i>06_patients_rag.py</i> (only)",
            body,
        )
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("Brief explanation (submission text)", h1))
    story.append(Paragraph(BRIEF_EXPLANATION, body))
    story.append(PageBreak())

    # Only the two assignment deliverables (no helper scripts)
    files_in_order = [
        ("System rules (YAML) — clinical tone and anti-hallucination constraints", "clinical_rag_rules.yaml"),
        ("Main RAG workflow — SQLite retrieval + JSON to LLM", "06_patients_rag.py"),
    ]

    for label, fname in files_in_order:
        fp = rag_dir / fname
        story.append(Paragraph(f"Source: <i>{fname}</i>", h1))
        story.append(Paragraph(label, h2))
        text = fp.read_text(encoding="utf-8")
        story.extend(code_block_paragraphs(text, code_style))
        story.append(PageBreak())

    story.append(Paragraph("Console output — answers to the four queries", h1))
    story.append(
        Paragraph(
            "Below is the terminal output from running <i>python 06_patients_rag.py</i> (demo mode). "
            "SQL retrieval lines print where applicable; Q4 also prints cohort aggregate hints. "
            "Narrative answers are model-generated summaries grounded in the JSON payload (and "
            "<i>summary_statistics</i> for Q4).",
            body,
        )
    )
    story.append(Spacer(1, 8))
    story.extend(code_block_paragraphs(CONSOLE_OUTPUT, code_style))

    doc.build(story)


def main() -> None:
    rag_dir = Path(__file__).resolve().parent
    out_path = rag_dir / "LAB_submission_custom_rag_patients.pdf"
    build_pdf(out_path, rag_dir)
    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
