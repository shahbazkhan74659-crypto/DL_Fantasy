import re
from io import BytesIO
from xml.sax.saxutils import escape

from django.utils import timezone
from django.utils.dateformat import format as format_date
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from upload.models import Content

PARAGRAPH_BREAK = re.compile(r'\n\s*\n')


def _display_title(content):
    if content.category == Content.Category.GODVALLEY and content.chapter_number:
        return f"Chapter {content.chapter_number} — {content.title}"
    return content.title


def build_content_pdf(content):
    """Render a Content row to a PDF byte string, on demand — the PDF is never stored server-side,
    only the fact that it was downloaded (see DownloadHistory)."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=1 * inch, bottomMargin=1 * inch, leftMargin=1 * inch, rightMargin=1 * inch,
        title=_display_title(content), author='Mr. Dex',
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ContentTitle', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=20, spaceAfter=6,
    )
    meta_style = ParagraphStyle(
        'ContentMeta', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=10,
        textColor=HexColor('#555555'), spaceAfter=24,
    )
    body_style = ParagraphStyle(
        'ContentBody', parent=styles['Normal'], fontName='Helvetica', fontSize=11.5, leading=18,
        spaceAfter=14, alignment=4,  # justified
    )

    meta_bits = [content.get_category_display(), format_date(content.created_at, 'F j, Y')]

    story = [
        Paragraph(escape(_display_title(content)), title_style),
        Paragraph(escape(' · '.join(meta_bits)), meta_style),
    ]

    for paragraph in PARAGRAPH_BREAK.split(content.body.strip()):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        html = escape(paragraph).replace('\n', '<br/>')
        story.append(Paragraph(html, body_style))

    story.append(Spacer(1, 24))
    story.append(Paragraph(
        escape(f"Downloaded from DL Fantasy on {format_date(timezone.now(), 'F j, Y')}."),
        meta_style,
    ))

    doc.build(story)
    return buffer.getvalue()
