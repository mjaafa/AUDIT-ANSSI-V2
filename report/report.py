import datetime
import os
from fpdf import FPDF


def _parse_desc(raw):
    """Split 'title : label | rule |' into (title, label, rule)."""
    parts = [p.strip() for p in raw.split('|')]
    text = parts[0] if parts else raw.strip()
    rule = parts[1] if len(parts) > 1 else ''
    title, sep, label = text.partition(':')
    if not sep:
        return '', text, rule
    return title.strip(), label.strip(), rule


def _status(r):
    return r.get('status', 'OK' if r['ok'] else 'KO')


def _counts(results):
    """Return (passed, failed, not_applicable)."""
    statuses = [_status(r) for r in results]
    return statuses.count('OK'), statuses.count('KO'), statuses.count('N/A')


def _group_by_title(results):
    """Yield (title, [(index, name, label, rule, status), ...]) keeping test order."""
    groups = []
    for i, r in enumerate(results, 1):
        title, label, rule = _parse_desc(r['description'])
        if not groups or groups[-1][0] != title:
            groups.append((title, []))
        groups[-1][1].append((i, r.get('name', ''), label, rule, _status(r)))
    return groups


def _pdf_safe(text):
    """Drop characters outside latin-1 so Helvetica never raises."""
    return text.encode('latin-1', errors='ignore').decode('latin-1')


def _fit(pdf, text, width):
    """Truncate text with '...' so it fits in a cell of the given width."""
    text = _pdf_safe(text)
    max_w = width - 2 * pdf.c_margin
    if pdf.get_string_width(text) <= max_w:
        return text
    while text and pdf.get_string_width(text + "...") > max_w:
        text = text[:-1]
    return text + "..."


class _AuditPDF(FPDF):
    def __init__(self, hostname, generated_at):
        super().__init__()
        self._hostname = hostname
        self._generated_at = generated_at

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "AUDIT ANSSI - Security Compliance Report", align="C")
        self.ln(10)
        self.set_font("Helvetica", "", 9)
        self.cell(0, 6, f"Host: {self._hostname}    Generated: {self._generated_at}",
                  align="C")
        self.ln(6)
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
    passed, failed, na = _counts(results)
    lines = [
        "# AUDIT ANSSI - Security Compliance Report",
        "",
        f"**Date:** {now.strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"**Host:** {hostname}  ",
        f"**Total:** {len(results)} | **Passed:** {passed} | **Failed:** {failed} | **N/A:** {na}",
        "",
        "---",
    ]
    for title, rows in _group_by_title(results):
        lines += [
            "",
            f"## {title or 'Other tests'}",
            "",
            "| # | Rule | Test | Description | Status |",
            "|---|------|------|-------------|--------|",
        ]
        for i, name, label, rule, status in rows:
            lines.append(f"| {i} | {rule} | {name} | {label} | {status} |")
    return "\n".join(lines) + "\n"


def _build_pdf(results, hostname, now, out_path):
    passed, failed, na = _counts(results)
    generated_at = now.strftime("%Y-%m-%d %H:%M:%S")

    pdf = _AuditPDF(hostname, generated_at)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Summary line
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8,
             f"Summary: {len(results)} checks - {passed} passed, {failed} failed, {na} not applicable")
    pdf.ln(8)
    pdf.ln(3)

    # Column widths (page width ~190 mm with default margins)
    COL = [10, 22, 70, 72, 16]
    ROW_H = 6

    for title, rows in _group_by_title(results):
        # Keep the section title on the same page as its first rows
        if pdf.get_y() + 10 + 3 * ROW_H > pdf.h - pdf.b_margin:
            pdf.add_page()

        # Section title
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, _pdf_safe(title or "Other tests"))
        pdf.ln(9)

        # Header row
        pdf.set_fill_color(50, 50, 50)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 9)
        for w, label in zip(COL, ["#", "Rule", "Test", "Description", "Status"]):
            pdf.cell(w, ROW_H, label, border=1, fill=True, align="C")
        pdf.ln()

        # Data rows
        pdf.set_font("Helvetica", "", 8)
        for i, name, label, rule, status in rows:
            if status == "OK":
                pdf.set_fill_color(232, 255, 232)
            elif status == "N/A":
                pdf.set_fill_color(240, 240, 240)
            else:
                pdf.set_fill_color(255, 232, 232)

            pdf.set_text_color(0, 0, 0)
            pdf.cell(COL[0], ROW_H, str(i), border=1, fill=True, align="R")
            pdf.cell(COL[1], ROW_H, _fit(pdf, rule, COL[1]), border=1, fill=True)
            pdf.cell(COL[2], ROW_H, _fit(pdf, name, COL[2]), border=1, fill=True)
            pdf.cell(COL[3], ROW_H, _fit(pdf, label, COL[3]), border=1, fill=True)

            if status == "OK":
                pdf.set_text_color(0, 130, 0)
            elif status == "N/A":
                pdf.set_text_color(110, 110, 110)
            else:
                pdf.set_text_color(180, 0, 0)
            pdf.cell(COL[4], ROW_H, status, border=1, fill=True, align="C")
            pdf.set_text_color(0, 0, 0)
            pdf.ln()
        pdf.ln(4)

    pdf.output(out_path)
