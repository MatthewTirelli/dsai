# build_ai_qc_pdf.py
# Build a PDF with full source of 02 + 04 and captured terminal output.
# Run from repo root:  python3 09_text_analysis/build_ai_qc_pdf.py
#
# Requires: pip install reportlab
#
# Notes:
# - Section 2 (02 output): prefers data/captured_02_stdout.txt, else live Ollama run,
#   else bundled data/pdf_embedded_02_demo_stdout.txt so the PDF is never empty.
# - Code and output are wrapped to a fixed character width so nothing clips horizontally.
# - Long content is split into chunks (paragraphs) so ReportLab does not overflow vertically.
# - Non-Latin-1 characters (e.g. some emoji) are replaced so built-in PDF fonts render reliably.

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

REPO_ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent

OUT_PDF = HERE / "AI_QC_code_and_output.pdf"
EMBEDDED_02 = HERE / "data" / "pdf_embedded_02_demo_stdout.txt"
HAND_02 = HERE / "data" / "captured_02_stdout.txt"

# Landscape letter gives more width for code; tune wrap width to match margins + font.
LS = landscape(letter)
MAX_CHARS_PER_LINE = 102
LINES_PER_CHUNK = 42
LEFT_RIGHT = 0.55 * inch
TOP_BOTTOM = 0.55 * inch


def strip_for_pdf(s: str) -> str:
    """Avoid missing glyphs in standard Helvetica/Courier (emoji, rare Unicode)."""
    out = []
    for ch in s:
        o = ord(ch)
        if ch in "\n\t\r":
            out.append(ch)
        elif 32 <= o <= 126:
            out.append(ch)
        else:
            out.append("?")
    return "".join(out)


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
    wrapped = wrap_fixed_width(strip_for_pdf(text))
    lines = wrapped.splitlines()
    chunks: list = []
    for i in range(0, len(lines), LINES_PER_CHUNK):
        block = lines[i : i + LINES_PER_CHUNK]
        body = "<br/>".join(escape_xml(line) for line in block)
        chunks.append(Paragraph(body, style))
        chunks.append(Spacer(1, 1))
    return chunks


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def capture_04() -> str:
    p = HERE / "04_qc_rubric_comparison.py"
    r = subprocess.run(
        [sys.executable, str(p)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    out = (r.stdout or "") + ("\n--- stderr ---\n" + r.stderr if r.stderr else "")
    if r.returncode != 0:
        out = f"[exit code {r.returncode}]\n" + out
    return out


def _capture_02_demo_run() -> str:
    """
    Run 02 with EXPORT_DUAL_QC_CSV forced False so the demo (two API calls) runs.
    Requires Ollama + model; may take minutes. On failure, returns an error string.
    """
    src_path = HERE / "02_ai_quality_control.py"
    src = src_path.read_text(encoding="utf-8")
    src_mod = re.sub(
        r"^EXPORT_DUAL_QC_CSV\s*=\s*\S+",
        "EXPORT_DUAL_QC_CSV = False",
        src,
        count=1,
        flags=re.MULTILINE,
    )
    tmp = HERE / "data" / "_tmp_02_for_pdf_build.py"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(src_mod, encoding="utf-8")
    try:
        r = subprocess.run(
            [sys.executable, str(tmp)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=600,
        )
        out = (r.stdout or "") + ("\n--- stderr ---\n" + r.stderr if r.stderr else "")
        if r.returncode != 0:
            out = f"[exit code {r.returncode}]\n" + out
        return out
    except subprocess.TimeoutExpired:
        return "[Timeout running 02_ai_quality_control.py — Ollama may be slow or unreachable.]"
    except Exception as e:
        return f"[Could not run 02 demo: {e}]"
    finally:
        tmp.unlink(missing_ok=True)


def _looks_like_failed_02_run(s: str) -> bool:
    if not s.strip():
        return True
    t = s.lstrip()
    if t.startswith("[exit code"):
        return True
    if t.startswith("[Timeout"):
        return True
    if t.startswith("[Could not run 02"):
        return True
    return False


def load_or_capture_02(skip_ollama: bool) -> tuple[str, str]:
    """
    Returns (stdout_text, short_provenance_note_for_cover_paragraph).
    Order: manual file > live Ollama (unless skip) > bundled embedded snapshot.
    """
    if HAND_02.is_file():
        return read_text(HAND_02), "Source: data/captured_02_stdout.txt (manual override)."

    if not skip_ollama:
        live = _capture_02_demo_run()
        if not _looks_like_failed_02_run(live):
            return live, "Source: live run while building this PDF (EXPORT_DUAL_QC_CSV = False; Ollama)."

    if EMBEDDED_02.is_file():
        return (
            read_text(EMBEDDED_02),
            "Source: data/pdf_embedded_02_demo_stdout.txt (bundled snapshot). "
            "For a fresh capture, run this script without --skip-ollama with Ollama up, "
            "or save stdout to data/captured_02_stdout.txt.",
        )

    return (
        "[No 02 output: add data/pdf_embedded_02_demo_stdout.txt or data/captured_02_stdout.txt.]\n",
        "Source: none available.",
    )


def build_pdf(*, skip_ollama: bool = False) -> None:
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleDoc",
        parent=styles["Title"],
        fontSize=16,
        spaceAfter=10,
        alignment=TA_LEFT,
    )
    h1 = ParagraphStyle(
        "H1Doc",
        parent=styles["Heading1"],
        fontSize=13,
        spaceBefore=10,
        spaceAfter=8,
        textColor=colors.HexColor("#1a1a1a"),
        alignment=TA_LEFT,
    )
    body = ParagraphStyle(
        "BodyDoc",
        parent=styles["Normal"],
        fontSize=10,
        leading=13,
        alignment=TA_LEFT,
    )
    # Landscape + 7.5pt Courier: readable, no heavy borders (avoids stacked boxes).
    code_style = ParagraphStyle(
        "CodeDoc",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=7.5,
        leading=9,
        leftIndent=0,
        rightIndent=0,
        spaceBefore=2,
        spaceAfter=4,
        backColor=colors.HexColor("#f7f7f7"),
        borderWidth=0,
        borderPadding=6,
        alignment=TA_LEFT,
    )

    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=LS,
        leftMargin=LEFT_RIGHT,
        rightMargin=LEFT_RIGHT,
        topMargin=TOP_BOTTOM,
        bottomMargin=TOP_BOTTOM,
        title="AI QC — code and output",
    )

    story: list = []

    story.append(
        Paragraph(
            "<b>AI-assisted quality control — source code and terminal output</b><br/>"
            "<i>09_text_analysis/02_ai_quality_control.py</i> and "
            "<i>04_qc_rubric_comparison.py</i>",
            title_style,
        )
    )
    story.append(
        Paragraph(
            "Landscape pages improve line length for code. Text is wrapped to "
            f"<b>{MAX_CHARS_PER_LINE}</b> characters per line. "
            "Non-ASCII symbols (e.g. emoji) may appear as <b>?</b> for reliable PDF fonts.",
            body,
        )
    )
    story.append(Spacer(1, 8))

    # --- 02 code ---
    story.append(Paragraph("Section 1 — Full source: <i>02_ai_quality_control.py</i>", h1))
    code_02 = read_text(HERE / "02_ai_quality_control.py")
    story.extend(monospace_chunks(code_02, code_style))
    story.append(PageBreak())

    # --- 02 output ---
    out02, prov02 = load_or_capture_02(skip_ollama)
    story.append(Paragraph("Section 2 — Terminal output: <i>02_ai_quality_control.py</i> (demo mode)", h1))
    story.append(
        Paragraph(
            "<b>How this section was produced.</b> "
            "The demo runs when <b>EXPORT_DUAL_QC_CSV = False</b> (both rubrics on the first report). "
            f"<br/><i>{escape_xml(prov02)}</i>",
            body,
        )
    )
    story.append(Spacer(1, 6))
    story.extend(monospace_chunks(out02, code_style))
    story.append(PageBreak())

    # --- 04 code ---
    story.append(Paragraph("Section 3 — Full source: <i>04_qc_rubric_comparison.py</i>", h1))
    code_04 = read_text(HERE / "04_qc_rubric_comparison.py")
    story.extend(monospace_chunks(code_04, code_style))
    story.append(PageBreak())

    # --- 04 output ---
    story.append(Paragraph("Section 4 — Terminal output: <i>04_qc_rubric_comparison.py</i>", h1))
    story.append(
        Paragraph(
            "Requires <i>09_text_analysis/data/qc_prompt_ab_scores.csv</i> "
            "(from 02 with <b>EXPORT_DUAL_QC_CSV = True</b>).",
            body,
        )
    )
    story.append(Spacer(1, 6))
    story.extend(monospace_chunks(capture_04(), code_style))

    doc.build(story)
    print(f"Wrote: {OUT_PDF.resolve()}")


if __name__ == "__main__":
    skip = "--skip-ollama" in sys.argv
    build_pdf(skip_ollama=skip)
