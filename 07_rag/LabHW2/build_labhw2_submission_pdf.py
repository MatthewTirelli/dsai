# build_labhw2_submission_pdf.py
# LabHW2 — Build submission PDF (code + markdown outputs)
# Pairs with labhw2_two_agent_patients.py
# Tim Fraser (course materials) / LabHW2 extension
#
# Generates a letter-size PDF with wrapped monospace chunks and page breaks so content
# is not clipped. Run after regenerating the .md files from the main lab script.
#
# Run from LabHW2:  python build_labhw2_submission_pdf.py
# Run from repo:    python 07_rag/LabHW2/build_labhw2_submission_pdf.py

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

# Optional: set before building
STUDENT_NAME = "Matthew Tirelli"

# Margins and wrapping — avoid horizontal/vertical cutoff (letter, generous margins)
LEFT_RIGHT = 0.85 * inch
TOP_BOTTOM = 0.75 * inch
# Slightly narrower than 06 lab PDF so wide markdown table lines wrap reliably
MAX_CHARS_PER_LINE = 82
# Smaller vertical chunks so ReportLab never chokes on one huge Paragraph
LINES_PER_CHUNK = 34


def wrap_fixed_width(text: str, width: int = MAX_CHARS_PER_LINE) -> str:
    """Hard-wrap long lines so nothing clips at the right edge."""
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


def monospace_chunks(text: str, style: ParagraphStyle) -> list:
    """Many small Paragraphs (wrapped Courier) — reliable for long code and markdown tables."""
    wrapped = wrap_fixed_width(text)
    lines = wrapped.splitlines()
    chunks: list = []
    for i in range(0, len(lines), LINES_PER_CHUNK):
        block = lines[i : i + LINES_PER_CHUNK]
        body = "<br/>".join(escape_xml(line) for line in block)
        chunks.append(Paragraph(body, style))
        chunks.append(Spacer(1, 3))
    return chunks


def build_pdf(lab_dir: Path, out_path: Path) -> None:
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "HW2Title",
        parent=styles["Title"],
        fontSize=16,
        spaceAfter=12,
        alignment=TA_LEFT,
    )
    h1 = ParagraphStyle(
        "HW2H1",
        parent=styles["Heading1"],
        fontSize=13,
        spaceBefore=14,
        spaceAfter=8,
        textColor=colors.HexColor("#1a1a1a"),
        alignment=TA_LEFT,
    )
    h2 = ParagraphStyle(
        "HW2H2",
        parent=styles["Heading2"],
        fontSize=11,
        spaceBefore=8,
        spaceAfter=6,
        alignment=TA_LEFT,
    )
    body = ParagraphStyle(
        "HW2Body",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        alignment=TA_LEFT,
    )
    code_style = ParagraphStyle(
        "HW2Code",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=6.5,
        leading=8,
        leftIndent=6,
        rightIndent=6,
        spaceBefore=4,
        spaceAfter=6,
        backColor=colors.HexColor("#f4f4f4"),
        borderColor=colors.grey,
        borderWidth=0.5,
        borderPadding=5,
        alignment=TA_LEFT,
    )

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=letter,
        leftMargin=LEFT_RIGHT,
        rightMargin=LEFT_RIGHT,
        topMargin=TOP_BOTTOM,
        bottomMargin=TOP_BOTTOM,
        title="LabHW2 — Function calling & two-agent workflow",
    )

    story: list = []

    story.append(Paragraph("LabHW2: Custom tool + two-agent workflow (submission)", title_style))
    meta_bits = [
        "<b>Assignment:</b> Custom tool, Agent 1 (tool cohort), Agent 2 (clinical synopsis).",
        "<b>Folder:</b> <i>07_rag/LabHW2/</i>",
    ]
    if STUDENT_NAME.strip():
        meta_bits.insert(0, f"<b>Student:</b> {escape_xml(STUDENT_NAME.strip())}")
    story.append(Paragraph("<br/>".join(meta_bits), body))
    story.append(Spacer(1, 10))

    story.append(Paragraph("What this PDF contains", h1))
    story.append(
        Paragraph(
            "<b>Section 1 — Local helper module (<i>functions.py</i>):</b> "
            "<i>agent</i>, <i>agent_run</i>, <i>df_as_text</i>, Ollama HTTP client, "
            "stack-walk tool dispatch, and recovery when models emit JSON-shaped tool text "
            "in <i>message.content</i> instead of native <i>tool_calls</i>.",
            body,
        )
    )
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "<b>Section 2 — Main workflow (<i>labhw2_two_agent_patients.py</i>):</b> "
            "SQLite tool <i>list_phq9_elevated_with_safety_concerns</i>, tool metadata, "
            "Agent 1 + Agent 2 prompts, and writes to the two markdown deliverables below.",
            body,
        )
    )
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "<b>Section 3 — Agent 1 output (<i>agent1_cohort_findings.md</i>):</b> "
            "Run metadata, cohort counts, and the full markdown table of qualifying visits "
            "(PHQ-9 &gt; 15 and safety_concerns = Y).",
            body,
        )
    )
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "<b>Section 4 — Agent 2 output (<i>clinical_findings_synopsis.md</i>):</b> "
            "One-page-style clinical synopsis generated by the second agent from the cohort summary.",
            body,
        )
    )
    story.append(PageBreak())

    files_code = [
        (
            "Section 1 — functions.py (LabHW2 copy: Ollama + tool execution)",
            "Helper module used by the main script. Defines how tools are resolved in the caller script "
            "and how assistant text that looks like a JSON tool call is recovered when needed.",
            "functions.py",
        ),
        (
            "Section 2 — labhw2_two_agent_patients.py (main submission script)",
            "Custom SQLite tool, tool JSON schema, two-agent chain via agent_run(), "
            "and paths to patients.db and output markdown files.",
            "labhw2_two_agent_patients.py",
        ),
    ]

    for section_title, blurb, fname in files_code:
        fp = lab_dir / fname
        if not fp.is_file():
            story.append(Paragraph(f"<b>Missing file:</b> {fname}", h1))
            story.append(PageBreak())
            continue
        story.append(Paragraph(escape_xml(section_title), h1))
        story.append(Paragraph(blurb, body))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"<i>File:</i> {escape_xml(fname)}", h2))
        text = fp.read_text(encoding="utf-8")
        story.extend(monospace_chunks(text, code_style))
        story.append(PageBreak())

    md_parts = [
        (
            "Section 3 — agent1_cohort_findings.md (Agent 1 deliverable)",
            "Written by the workflow after Agent 1: metadata, cohort rule, visit/patient counts, "
            "and the full cohort table (all columns). Rendered below as wrapped monospace to preserve table structure.",
            "agent1_cohort_findings.md",
        ),
        (
            "Section 4 — clinical_findings_synopsis.md (Agent 2 deliverable)",
            "Markdown synopsis from Agent 2 (clinical chart review style) based on the cohort passed in the prompt.",
            "clinical_findings_synopsis.md",
        ),
    ]

    for section_title, blurb, fname in md_parts:
        fp = lab_dir / fname
        story.append(Paragraph(escape_xml(section_title), h1))
        story.append(Paragraph(blurb, body))
        story.append(Spacer(1, 6))
        if not fp.is_file():
            story.append(
                Paragraph(
                    f"<i>File not found:</i> {escape_xml(fname)} — run "
                    "<i>python labhw2_two_agent_patients.py</i> first, then rebuild this PDF.",
                    body,
                )
            )
        else:
            story.append(Paragraph(f"<i>File:</i> {escape_xml(fname)}", h2))
            text = fp.read_text(encoding="utf-8")
            story.extend(monospace_chunks(text, code_style))
        story.append(PageBreak())

    # Remove trailing blank page from last PageBreak
    if story and isinstance(story[-1], PageBreak):
        story.pop()

    doc.build(story)


def main() -> None:
    lab_dir = Path(__file__).resolve().parent
    out_path = lab_dir / "LabHW2_function_calling_submission.pdf"
    build_pdf(lab_dir, out_path)
    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
