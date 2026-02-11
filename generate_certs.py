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
    },
    "Abode": {
        "org_name": "Abode Care Service Coordination",
        "trainer_name": "Lipa Lefkowitz",
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
    # "Name of Staff" is at y ratio 0.723 (PDF y ≈ 390)
    name_y = ph * 0.695
    c.setFillColor(HexColor("#FFFFFF"))
    c.rect(pw * 0.25, name_y - 5, pw * 0.5, 25, fill=True, stroke=False)

    # ── Staff name — use Times-BoldItalic to match Palatino BoldItalic ──
    c.setFont("Times-BoldItalic", 26)
    c.setFillColor(HexColor("#CC0000"))
    c.drawCentredString(pw / 2, name_y, staff_name)

    # ── If Abode: white-out and replace org name + trainer ───────────
    if agency == "Abode":
        c.saveState()
        # "Attentive Care Service Coordination" at y ratio 0.826
        c.setFillColor(HexColor("#FFFFFF"))
        c.setStrokeColor(HexColor("#FFFFFF"))
        c.rect(pw * 0.15, ph * 0.795, pw * 0.7, ph * 0.04, fill=True, stroke=True)
        c.setFont("Times-BoldItalic", 11)
        c.setFillColor(HexColor("#333333"))
        c.drawCentredString(pw / 2, ph * 0.805, cfg["org_name"])

        # "Joel Posen" at y ratio 0.270
        c.setFillColor(HexColor("#FFFFFF"))
        c.setStrokeColor(HexColor("#FFFFFF"))
        c.rect(pw * 0.06, ph * 0.235, pw * 0.3, ph * 0.04, fill=True, stroke=True)
        c.setFont("Times-Roman", 11)
        c.setFillColor(HexColor("#000000"))
        c.drawString(pw * 0.1, ph * 0.249, cfg["trainer_name"])
        c.restoreState()

    # ── Completion date — ON the underline after "Completion Date: ___"
    # Underscores at x=311-507, y_ratio=0.329. Place date centered on them.
    c.setFont("Times-Bold", 12)
    c.setFillColor(HexColor("#000000"))
    c.drawCentredString((311 + 507) / 2, ph * 0.318, completion_date)

    # ── Signature date — above the sig line, over the "Date" label
    # Sig line at y_ratio=0.231, "Date" label at y_ratio=0.211
    c.setFont("Times-Roman", 11)
    c.drawCentredString(pw * 0.82, ph * 0.237, sig_date)

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
