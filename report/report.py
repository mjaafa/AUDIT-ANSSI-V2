import datetime
import os
from fpdf import FPDF


def _parse_desc(raw):
    parts = [p.strip() for p in raw.split('|')]
    label = parts[0].strip() if parts else raw.strip()
    rule = parts[1].strip() if len(parts) > 1 else ''
    return label, rule


def _pdf_safe(text):
    """Drop characters outside latin-1 so Helvetica never raises."""
    return text.encode('latin-1', errors='ignore').decode('latin-1')


class _AuditPDF(FPDF):
    def __init__(self, hostname, generated_at):
        super().__init__()
        self._hostname = hostname
        self._generated_at = generated_at

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "AUDIT ANSSI - Security Compliance Report",
                  align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.cell(0, 6, f"Host: {self._hostname}    Generated: {self._generated_at}",
                  align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def generate(results, hostname, out_dir="reports"):
    """Write .md and .pdf audit reports. Returns (md_path, pdf_path)."""
    now = datetime.datetime.now()
    ts = now.strftime("%Y%m%d_%H%M%S")
    os.makedirs(out_dir, exist_ok=True)

    md_path = os.path.join(out_dir, f"audit_{ts}.md")
    pdf_path = os.path.join(out_dir, f"audit_{ts}.pdf")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(_build_md(results, hostname, now))

    _build_pdf(results, hostname, now, pdf_path)

    return md_path, pdf_path


def _build_md(results, hostname, now):
    passed = sum(1 for r in results if r['ok'])
    failed = len(results) - passed
    lines = [
        "# AUDIT ANSSI - Security Compliance Report",
        "",
        f"**Date:** {now.strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"**Host:** {hostname}  ",
        f"**Total:** {len(results)} | **Passed:** {passed} | **Failed:** {failed}",
        "",
        "---",
        "",
        "| # | Rule | Description | Status |",
        "|---|------|-------------|--------|",
    ]
    for i, r in enumerate(results, 1):
        label, rule = _parse_desc(r['description'])
        status = "OK" if r['ok'] else "KO"
        lines.append(f"| {i} | {rule} | {label} | {status} |")
    return "\n".join(lines) + "\n"


def _build_pdf(results, hostname, now, out_path):
    passed = sum(1 for r in results if r['ok'])
    failed = len(results) - passed
    generated_at = now.strftime("%Y-%m-%d %H:%M:%S")

    pdf = _AuditPDF(hostname, generated_at)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Summary line
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8,
             f"Summary: {len(results)} checks - {passed} passed, {failed} failed",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Column widths (page width ~190 mm with default margins)
    COL = [10, 28, 134, 18]
    ROW_H = 6

    # Header row
    pdf.set_fill_color(50, 50, 50)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    for w, label in zip(COL, ["#", "Rule", "Description", "Status"]):
        pdf.cell(w, ROW_H, label, border=1, fill=True, align="C")
    pdf.ln()

    # Data rows
    pdf.set_font("Helvetica", "", 8)
    for i, r in enumerate(results, 1):
        label, rule = _parse_desc(r['description'])
        status = "OK" if r['ok'] else "KO"

        if r['ok']:
            pdf.set_fill_color(232, 255, 232)
        else:
            pdf.set_fill_color(255, 232, 232)

        pdf.set_text_color(0, 0, 0)
        pdf.cell(COL[0], ROW_H, str(i), border=1, fill=True, align="R")
        pdf.cell(COL[1], ROW_H, _pdf_safe(rule[:24]), border=1, fill=True)
        pdf.cell(COL[2], ROW_H, _pdf_safe(label[:75]), border=1, fill=True)

        if r['ok']:
            pdf.set_text_color(0, 130, 0)
        else:
            pdf.set_text_color(180, 0, 0)
        pdf.cell(COL[3], ROW_H, status, border=1, fill=True, align="C")
        pdf.set_text_color(0, 0, 0)
        pdf.ln()

    pdf.output(out_path)
