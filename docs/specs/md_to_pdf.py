#!/usr/bin/env python3
"""Convert a simple Markdown case-study definition into a professional PDF."""
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                ListFlowable, ListItem)
from reportlab.lib.enums import TA_LEFT

PRIMARY = HexColor("#714B67")
LIGHT = HexColor("#875A7A")
MUTED = HexColor("#6b7280")

INPUT = "/home/denispy/project-agent-system/specs/ProjectManagementAI-CaseStudy-Definition-v1.0.md"
OUTPUT = "/home/denispy/project-agent-system/specs/ProjectManagementAI-CaseStudy-Definition-v1.0.pdf"


def build_styles():
    styles = getSampleStyleSheet()

    # Safe helper that replaces existing style if name exists
    def safe_add(name, style):
        if name in styles:
            styles.byName[name] = style
        else:
            styles.add(style)

    safe_add("DocTitle", ParagraphStyle(
        name="DocTitle", parent=styles["Title"],
        fontName="Helvetica-Bold", fontSize=22,
        textColor=PRIMARY, spaceAfter=14, leading=26))

    safe_add("H1", ParagraphStyle(
        name="H1", parent=styles["Heading1"],
        fontName="Helvetica-Bold", fontSize=16,
        textColor=PRIMARY, spaceBefore=18, spaceAfter=10, leading=20))

    safe_add("H2", ParagraphStyle(
        name="H2", parent=styles["Heading2"],
        fontName="Helvetica-Bold", fontSize=13,
        textColor=LIGHT, spaceBefore=14, spaceAfter=8, leading=16))

    safe_add("H3", ParagraphStyle(
        name="H3", parent=styles["Heading3"],
        fontName="Helvetica-Bold", fontSize=11,
        textColor=LIGHT, spaceBefore=10, spaceAfter=6, leading=14))

    safe_add("CaseBody", ParagraphStyle(
        name="CaseBody", parent=styles["BodyText"],
        fontName="Helvetica", fontSize=10.5,
        textColor=colors.black, leading=15,
        spaceAfter=6, alignment=TA_LEFT))

    safe_add("CaseBullet", ParagraphStyle(
        name="CaseBullet", parent=styles["BodyText"],
        fontName="Helvetica", fontSize=10.5,
        textColor=colors.black, leading=15,
        leftIndent=14, bulletIndent=4, spaceAfter=4))

    safe_add("CaseMeta", ParagraphStyle(
        name="CaseMeta", parent=styles["BodyText"],
        fontName="Helvetica-Oblique", fontSize=9.5,
        textColor=MUTED, leading=13, spaceAfter=4))

    return styles


def parse_markdown(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def render_pdf(md_text, output_path):
    styles = build_styles()
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title="AI Project Management Ecosystem — Case Study Definition",
        author="Denilson Fragoso Da Silva Santos")

    story = []
    lines = md_text.split("\n")
    i = 0
    bullet_items = []

    def flush_bullets():
        nonlocal bullet_items
        if bullet_items:
            items = [ListItem(Paragraph(t, styles["CaseBullet"]))
                     for t in bullet_items]
            story.append(ListFlowable(items, bulletType="bullet", leftIndent=14))
            story.append(Spacer(1, 6))
            bullet_items = []

    while i < len(lines):
        line = lines[i].rstrip()

        if line.strip() == "---":
            flush_bullets()
            story.append(Spacer(1, 8))
            i += 1
            continue

        if line.startswith("# "):
            flush_bullets()
            story.append(Paragraph(line[2:].strip(), styles["DocTitle"]))
            i += 1
            continue

        if line.startswith("## "):
            flush_bullets()
            story.append(Paragraph(line[3:].strip(), styles["H1"]))
            i += 1
            continue

        if line.startswith("### "):
            flush_bullets()
            story.append(Paragraph(line[4:].strip(), styles["H2"]))
            i += 1
            continue

        if line.lstrip().startswith("- "):
            bullet_items.append(line.lstrip()[2:].strip())
            i += 1
            continue

        m = re.match(r"^\s*\d+\.\s+(.*)$", line)
        if m:
            bullet_items.append(m.group(1).strip())
            i += 1
            continue

        if not line.strip():
            flush_bullets()
            i += 1
            continue

        flush_bullets()
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line)
        story.append(Paragraph(text, styles["CaseBody"]))
        i += 1

    flush_bullets()
    doc.build(story)
    print(f"✅ PDF gerado: {output_path}")


if __name__ == "__main__":
    md = parse_markdown(INPUT)
    render_pdf(md, OUTPUT)
