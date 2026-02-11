#!/usr/bin/env python3
"""
Generate completion certificates.
Uses separate template PDFs for Attentive and Abode agencies.
"""
import sys, os, json
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from pypdf import PdfReader, PdfWriter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

AGENCY_CONFIG = {
    "Attentive": {
        "template": os.path.join(SCRIPT_DIR, "templates", "CERTIFICATE-_Attentive_JP.pdf"),
        "trainer_name": "Joel Posen",
        # "SC Supervisor/Director" ends at x=494.7, baseline y=131.5
        "title_end_x": 494.7,
        "title_baseline_y": 131.5,
    },
    "Abode": {
        "template": os.path.join(SCRIPT_DIR, "templates", "CERTIFICATE-_Abode_Fishel.pdf"),
        "trainer_name": "Lipa Lefkowitz",
        # "SC Supervisor" ends at x=457.8, baseline y=136.7
        "title_end_x": 457.8,
        "title_baseline_y": 136.7,
    }
}


def create_overlay(staff_name, completion_date, sig_date, agency="Attentive"):
    cfg = AGENCY_CONFIG.get(agency, AGENCY_CONFIG["Attentive"])
    template_path = os.environ.get("TEMPLATE_PDF", cfg["template"])
    reader = PdfReader(template_path)
    page = reader.pages[0]
    pw = float(page.mediabox.width)
    ph = float(page.mediabox.height)

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(pw, ph))

    # ── White-out original "Name of Staff" ────────────────────────────
    name_y = ph * 0.695
    c.setFillColor(HexColor("#FFFFFF"))
    c.rect(pw * 0.25, name_y - 5, pw * 0.5, 25, fill=True, stroke=False)

    # ── Staff name ────────────────────────────────────────────────────
    c.setFont("Times-BoldItalic", 26)
    c.setFillColor(HexColor("#CC0000"))
    c.drawCentredString(pw / 2, name_y, staff_name)

    # ── White-out original trainer name and write new one ─────────────
    if agency == "Abode":
        # White-out "Fishel Deutsch"
        c.setFillColor(HexColor("#FFFFFF"))
        c.setStrokeColor(HexColor("#FFFFFF"))
        c.rect(145, 132, 100, 22, fill=True, stroke=True)
        c.rect(145, 132, 100, 22, fill=True, stroke=True)
        c.setFont("Times-Roman", 11)
        c.setFillColor(HexColor("#000000"))
        c.drawString(158, 142.5, cfg["trainer_name"])

    # ── Completion date on the underline ──────────────────────────────
    # Underscores span x=311 to x=507
    c.setFont("Times-Bold", 12)
    c.setFillColor(HexColor("#000000"))
    c.drawCentredString((311 + 507) / 2, ph * 0.318, completion_date)

    # ── Signature date — inline on same baseline as title text ────────
    date_x = cfg["title_end_x"] + 16
    date_y = cfg["title_baseline_y"]
    c.setFont("Times-Roman", 11)
    c.drawString(date_x, date_y, sig_date)

    c.save()
    return buf.getvalue()


def generate_certificate(staff_name, completion_date, output_path, agency="Attentive"):
    cfg = AGENCY_CONFIG.get(agency, AGENCY_CONFIG["Attentive"])
    template_path = os.environ.get("TEMPLATE_PDF", cfg["template"])
    
    overlay_bytes = create_overlay(staff_name, completion_date, completion_date, agency)
    template_reader = PdfReader(template_path)
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
        print("Usage: python3 generate_certs.py <staff_name> <rows_json_path> [output_dir] [agency]")
        sys.exit(1)

    staff_name = sys.argv[1]
    rows_json  = sys.argv[2]
    out_dir    = sys.argv[3] if len(sys.argv) > 3 else "./output"
    agency     = sys.argv[4] if len(sys.argv) > 4 else "Attentive"

    os.makedirs(out_dir, exist_ok=True)
    with open(rows_json) as f:
        rows = json.load(f)

    safe_name = staff_name.replace(" ", "_")
    for row in rows:
        cert_date = row["certDate"]
        date_str = cert_date.replace("/", "-")
        out_path = os.path.join(out_dir, f"{safe_name}_Certificate_{date_str}.pdf")
        generate_certificate(staff_name, cert_date, out_path, agency)

    print(f"\nAll {len(rows)} certificates generated in {out_dir}/")


if __name__ == "__main__":
    main()
