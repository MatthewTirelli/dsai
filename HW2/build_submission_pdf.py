# build_submission_pdf.py
# Homework 2 — Build submission PDF (code + markdown/JSON outputs)
# Run from HW2/:  python build_submission_pdf.py
# Requires: pip install reportlab

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

STUDENT_NAME = "Matthew Tirelli"

LEFT_RIGHT = 0.85 * inch
TOP_BOTTOM = 0.75 * inch
MAX_CHARS_PER_LINE = 82
LINES_PER_CHUNK = 34


def wrap_fixed_width(text: str, width: int = MAX_CHARS_PER_LINE) -> str:
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
    wrapped = wrap_fixed_width(text)
    lines = wrapped.splitlines()
    chunks: list = []
    for i in range(0, len(lines), LINES_PER_CHUNK):
        block = lines[i : i + LINES_PER_CHUNK]
        body = "<br/>".join(escape_xml(line) for line in block)
        chunks.append(Paragraph(body, style))
        chunks.append(Spacer(1, 3))
    return chunks


def build_pdf(hw_dir: Path, out_path: Path) -> None:
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
        title="Homework 2 — Agents, RAG, tools",
    )

    story: list = []

    story.append(Paragraph("Homework 2: Multi-agent + RAG + function calling (submission)", title_style))
    meta_bits = [
        "<b>Assignment:</b> Agent 1 tool cohort + trace, RAG payload + verification, Agent 2 report.",
        "<b>Folder:</b> <i>HW2/</i>",
    ]
    if STUDENT_NAME.strip():
        meta_bits.insert(0, f"<b>Student:</b> {escape_xml(STUDENT_NAME.strip())}")
    story.append(Paragraph("<br/>".join(meta_bits), body))
    story.append(Spacer(1, 10))

    story.append(Paragraph("What this PDF contains", h1))
    story.append(
        Paragraph(
            "<b>Section 1 — functions.py:</b> Ollama client, <i>agent_run</i>, tool dispatch, "
            "recovery when models emit JSON-shaped tool text in <i>message.content</i>.",
            body,
        )
    )
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "<b>Section 2 — retrieval.py:</b> Cohort-scoped SQL + JSON payload builders (RAG layer).",
            body,
        )
    )
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "<b>Section 3 — clinical_pipeline.py:</b> Tool definition, Agent 1 + Agent 2 orchestration.",
            body,
        )
    )
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "<b>Section 4 — outputs under <i>out/</i>:</b> Agent 1 markdown, tool trace JSON, "
            "retrieval payload + verification, Agent 2 report.",
            body,
        )
    )
    story.append(PageBreak())

    files_code = [
        (
            "Section 1 — functions.py",
            "Ollama HTTP helper module for this folder.",
            "functions.py",
        ),
        (
            "Section 2 — retrieval.py",
            "Cohort analytics and retrieval payload.",
            "retrieval.py",
        ),
        (
            "Section 3 — clinical_pipeline.py",
            "Pipeline module: tool, retrieval, two agents.",
            "clinical_pipeline.py",
        ),
    ]

    for section_title, blurb, fname in files_code:
        fp = hw_dir / fname
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

    out_dir = hw_dir / "out"
    md_parts = [
        (
            "Section 4a — out/agent1_cohort_findings.md",
            "Agent 1 deliverable: cohort table plus function-calling verification section.",
            out_dir / "agent1_cohort_findings.md",
        ),
        (
            "Section 4b — out/agent1_tool_trace.json",
            "Structured trace: native tool_calls vs content JSON recovery; tool output summaries.",
            out_dir / "agent1_tool_trace.json",
        ),
        (
            "Section 4c — out/retrieval_payload.json",
            "Deterministic retrieval JSON passed to Agent 2.",
            out_dir / "retrieval_payload.json",
        ),
        (
            "Section 4d — out/retrieval_verification.md",
            "Pass/fail checks linking cohort IDs, payload fields, and independent SQL.",
            out_dir / "retrieval_verification.md",
        ),
        (
            "Section 4e — out/retrieval_verification.json",
            "Structured RAG verification (same checks as the markdown file).",
            out_dir / "retrieval_verification.json",
        ),
        (
            "Section 4f — out/homework2_comprehensive_report.md",
            "Agent 2 clinical + administrative report.",
            out_dir / "homework2_comprehensive_report.md",
        ),
    ]

    for section_title, blurb, fp in md_parts:
        story.append(Paragraph(escape_xml(section_title), h1))
        story.append(Paragraph(blurb, body))
        story.append(Spacer(1, 6))
        if not fp.is_file():
            story.append(
                Paragraph(
                    f"<i>File not found:</i> {escape_xml(fp.name)} — run "
                    "<i>python clinical_pipeline.py</i> or the Shiny app first, then rebuild this PDF.",
                    body,
                )
            )
        else:
            story.append(Paragraph(f"<i>File:</i> {escape_xml(fp.name)}", h2))
            text = fp.read_text(encoding="utf-8")
            story.extend(monospace_chunks(text, code_style))
        story.append(PageBreak())

    if story and isinstance(story[-1], PageBreak):
        story.pop()

    doc.build(story)


def main() -> None:
    hw_dir = Path(__file__).resolve().parent
    out_path = hw_dir / "Homework2_submission.pdf"
    build_pdf(hw_dir, out_path)
    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
