"""Export itinerary as Markdown or PDF."""

from __future__ import annotations

from io import BytesIO
import re


def _xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def export_markdown(final_markdown: str, *, title: str = "trip-itinerary") -> tuple[bytes, str]:
    content = final_markdown.strip() + "\n"
    if not content.startswith("#"):
        content = f"# {title}\n\n{content}"
    filename = f"{title.replace(' ', '-').lower()}.md"
    return content.encode("utf-8"), filename


def export_pdf(final_markdown: str, *, title: str = "Trip Itinerary") -> tuple[bytes, str]:
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except ImportError as e:
        raise ImportError(
            "reportlab required for PDF export. Install with: pip install -e \".[voice]\""
        ) from e

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"]), Spacer(1, 12)]

    for line in final_markdown.splitlines():
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 6))
            continue
        safe = _xml_escape(stripped)
        # ReportLab Paragraph chokes on very long unbroken strings.
        if len(safe) > 2000:
            for chunk in re.findall(r".{1,2000}", safe):
                story.append(Paragraph(chunk, styles["Normal"]))
            continue
        if stripped.startswith("## "):
            story.append(Paragraph(safe[3:], styles["Heading2"]))
        elif stripped.startswith("### "):
            story.append(Paragraph(safe[4:], styles["Heading3"]))
        elif stripped.startswith("- "):
            story.append(Paragraph(f"• {safe[2:]}", styles["Normal"]))
        else:
            story.append(Paragraph(safe, styles["Normal"]))

    doc.build(story)
    filename = f"{title.replace(' ', '-').lower()}.pdf"
    return buffer.getvalue(), filename


def reportlab_available() -> bool:
    try:
        import reportlab  # noqa: F401

        return True
    except ImportError:
        return False
