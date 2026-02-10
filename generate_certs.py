#!/usr/bin/env python3
"""
Generate completion certificates by overlaying staff name, completion date,
and signature date onto the PDF template.
"""
import sys
import json
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.colors import HexColor
from pypdf import PdfReader, PdfWriter

TEMPLATE_PDF = os.environ.get(
    "TEMPLATE_PDF",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "CERTIFICATE-_Attentive_JP.pdf")
)


def create_overlay(staff_name: str, completion_date: str, sig_date: str) -> bytes:
    """Create a transparent PDF overlay with the dynamic text."""
    buf = BytesIO()
    # Match the template page size (landscape letter-ish from the original)
    reader = PdfReader(TEMPLATE_PDF)
    page = reader.pages[0]
    pw = float(page.mediabox.width)
    ph = float(page.mediabox.height)

    c = canvas.Canvas(buf, pagesize=(pw, ph))

    # ── White-out the original "Name of Staff" text ──────────────────
    name_y_center = ph * 0.685
    c.setFillColor(HexColor("#FFFFFF"))
    c.rect(pw * 0.3, name_y_center - 8, pw * 0.4, 30, fill=True, stroke=False)

    # ── Staff name (red, bold italic, centered, same position) ───────
    c.setFont("Helvetica-BoldOblique", 22)
    c.setFillColor(HexColor("#CC0000"))
    c.drawCentredString(pw / 2, name_y_center, staff_name)

    # ── Completion date (black, on the "Completion Date: ___" line) ──
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(HexColor("#000000"))
    date_y = ph * 0.273
    c.drawString(pw * 0.465, date_y, completion_date)

    # ── Signature date (below "Date" label at bottom right) ──────────
    c.setFont("Helvetica", 11)
    sig_date_y = ph * 0.168
    c.drawString(pw * 0.76, sig_date_y, sig_date)

    c.save()
    return buf.getvalue()


def generate_certificate(staff_name: str, completion_date: str, output_path: str):
    """Merge overlay onto template and save."""
    overlay_bytes = create_overlay(staff_name, completion_date, completion_date)

    template_reader = PdfReader(TEMPLATE_PDF)
    overlay_reader = PdfReader(BytesIO(overlay_bytes))

    writer = PdfWriter()
    bg_page = template_reader.pages[0]
    bg_page.merge_page(overlay_reader.pages[0])
    writer.add_page(bg_page)

    with open(output_path, "wb") as f:
        writer.write(f)
    print(f"CERT created: {output_path}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 generate_certs.py <staff_name> <rows_json_path> <output_dir>")
        sys.exit(1)

    staff_name = sys.argv[1]
    rows_json  = sys.argv[2]
    out_dir    = sys.argv[3] if len(sys.argv) > 3 else "./output"

    os.makedirs(out_dir, exist_ok=True)

    with open(rows_json) as f:
        rows = json.load(f)

    safe_name = staff_name.replace(" ", "_")
    for i, row in enumerate(rows):
        cert_date = row["certDate"]
        # Sanitize date for filename
        date_str = cert_date.replace("/", "-")
        out_path = os.path.join(out_dir, f"{safe_name}_Certificate_{date_str}.pdf")
        generate_certificate(staff_name, cert_date, out_path)

    print(f"\nAll {len(rows)} certificates generated in {out_dir}/")


if __name__ == "__main__":
    main()
