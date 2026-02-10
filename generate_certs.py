#!/usr/bin/env python3
"""
Generate completion certificates. Supports Attentive and Abode agencies.
"""
import sys, os, json
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from pypdf import PdfReader, PdfWriter

TEMPLATE_PDF = os.environ.get(
    "TEMPLATE_PDF",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "CERTIFICATE-_Attentive_JP.pdf")
)

AGENCY_CONFIG = {
    "Attentive": {
        "org_name": "Attentive Care Service Coordination",
        "trainer_name": "Joel Posen",
        "trainer_title": "SC Supervisor/Director",
    },
    "Abode": {
        "org_name": "Abode Care Service Coordination",
        "trainer_name": "Lipa Lefkowitz",
        "trainer_title": "SC Supervisor/Director",
    }
}


def create_overlay(staff_name, completion_date, sig_date, agency="Attentive"):
    cfg = AGENCY_CONFIG.get(agency, AGENCY_CONFIG["Attentive"])
    reader = PdfReader(TEMPLATE_PDF)
    page = reader.pages[0]
    pw = float(page.mediabox.width)
    ph = float(page.mediabox.height)

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(pw, ph))

    # ── White-out original "Name of Staff" text ──────────────────────
    name_y_center = ph * 0.685
    c.setFillColor(HexColor("#FFFFFF"))
    c.rect(pw * 0.3, name_y_center - 8, pw * 0.4, 30, fill=True, stroke=False)

    # ── Staff name (red, bold italic, centered) ──────────────────────
    c.setFont("Helvetica-BoldOblique", 22)
    c.setFillColor(HexColor("#CC0000"))
    c.drawCentredString(pw / 2, name_y_center, staff_name)

    # ── If Abode: white-out and replace org name at top + trainer ───────
    if agency == "Abode":
        c.saveState()

        # "Attentive Care Service Coordination" is at PDF y=434.9-445.9
        c.setFillColor(HexColor("#FFFFFF"))
        c.setStrokeColor(HexColor("#FFFFFF"))
        c.rect(pw * 0.15, ph * 0.795, pw * 0.7, ph * 0.04, fill=True, stroke=True)
        c.setFont("Helvetica-Oblique", 12)
        c.setFillColor(HexColor("#333333"))
        c.drawCentredString(pw / 2, ph * 0.805, cfg["org_name"])

        # "Joel Posen" is at PDF y=134.7-145.7
        c.setFillColor(HexColor("#FFFFFF"))
        c.setStrokeColor(HexColor("#FFFFFF"))
        c.rect(pw * 0.06, ph * 0.235, pw * 0.3, ph * 0.04, fill=True, stroke=True)
        c.setFont("Helvetica", 12)
        c.setFillColor(HexColor("#000000"))
        c.drawString(pw * 0.1, ph * 0.249, cfg["trainer_name"])

        c.restoreState()

    # ── Completion date ──────────────────────────────────────────────
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(HexColor("#000000"))
    c.drawString(pw * 0.465, ph * 0.273, completion_date)

    # ── Signature date ───────────────────────────────────────────────
    c.setFont("Helvetica", 11)
    c.drawString(pw * 0.76, ph * 0.168, sig_date)

    c.save()
    return buf.getvalue()


def generate_certificate(staff_name, completion_date, output_path, agency="Attentive"):
    overlay_bytes = create_overlay(staff_name, completion_date, completion_date, agency)
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
