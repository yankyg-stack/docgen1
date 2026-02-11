#!/usr/bin/env python3
"""
Generate pre-test and post-test PDFs using ReportLab overlay approach.
Draws text and checkmarks directly instead of using form field filling.
"""
import sys, os, json, random
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from pypdf import PdfReader, PdfWriter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

TEST_TEMPLATES = {
    "Attentive": os.path.join(SCRIPT_DIR, "templates", "SC_Testing_Attentive_Final.pdf"),
    "Abode": os.path.join(SCRIPT_DIR, "templates", "SC_Testing_Abode_Final.pdf"),
}

def get_template(agency="Attentive"):
    env_val = os.environ.get("TEMPLATE_PDF_TEST")
    if env_val:
        return env_val
    return TEST_TEMPLATES.get(agency, TEST_TEMPLATES["Attentive"])


PAGE1_FIELDS = {"1_A","1_B","2_T","2_F","3_A","3_B","4_A","4_B","4_C",
                "5_T","5_F","T_3","6_T","6_F","7_T","7_F","8_T","8_F"}

# Field positions: {field_id: (x_center, y_center, width, height, page)}
FIELD_POS = {
    "1_A": (179.9, 546.4, 116.6, 12.1, 1), "1_B": (438.4, 546.4, 155.4, 12.1, 1),
    "2_T": (379.6, 507.7, 10.0, 10.0, 1),   "2_F": (404.0, 507.6, 10.0, 10.0, 1),
    "3_B": (418.6, 474.5, 114.5, 11.8, 1),   "3_A": (170.2, 462.4, 94.3, 15.1, 1),
    "4_A": (126.7, 385.1, 10.1, 10.1, 1),    "4_B": (126.5, 348.7, 10.1, 10.1, 1),
    "4_C": (126.6, 298.9, 10.0, 9.9, 1),
    "5_T": (158.8, 236.2, 10.0, 9.9, 1),     "5_F": (136.0, 235.9, 9.8, 9.9, 1),
    "6_T": (173.1, 186.3, 10.2, 9.9, 1),     "6_F": (197.7, 186.4, 9.8, 10.0, 1),
    "7_T": (348.8, 149.9, 9.9, 10.0, 1),     "7_F": (373.4, 149.8, 10.0, 10.0, 1),
    "8_T": (224.5, 100.3, 9.7, 9.9, 1),      "8_F": (248.9, 100.3, 10.1, 10.1, 1),
    "9_T": (180.9, 663.3, 10.0, 10.0, 2),    "9_F": (205.4, 663.3, 10.0, 10.0, 2),
    "10_T": (126.6, 613.5, 9.9, 10.0, 2),    "10_F": (151.0, 613.6, 10.0, 10.0, 2),
    "11_A": (342.2, 592.7, 105.5, 12.0, 2),  "11_B": (397.7, 579.5, 149.9, 12.0, 2),
    "12_T": (170.4, 527.7, 4.9, 6.4, 2),     "12_F": (192.2, 527.6, 4.8, 6.4, 2),
    "13_A": (236.0, 506.6, 189.0, 12.0, 2),
    "14_T": (260.4, 441.6, 4.9, 6.5, 2),     "14_F": (282.3, 441.7, 4.9, 6.3, 2),
    "15_A": (408.9, 420.5, 138.8, 12.0, 2),
    "16\u00ad_T": (125.4, 355.4, 4.8, 6.4, 2), "16_F": (147.2, 355.4, 5.0, 6.3, 2),
}

# NOTE on Q5: Field "5_F" is physically at the T checkbox position (left),
# and "5_T" is physically at the F position (right). Names are swapped in the PDF.
# So for Q5 correct answer FALSE: we check "5_T" (which is the visual F box).
ANSWER_KEY = [
    {"type": "text", "id": "1_A", "correct": "regulatory risk",
     "wrong": ["patient satisfaction", "employee turnover", "budget concerns", "compliance", "staffing issues"],
     "difficulty": 0.4},
    {"type": "text", "id": "1_B", "correct": "non-compliance",
     "wrong": ["employee dissatisfaction", "budget shortfalls", "turnover", "legal issues"],
     "difficulty": 0.4},
    {"type": "checkbox_pair", "correct_id": "2_T", "wrong_id": "2_F", "difficulty": 0.3},
    {"type": "text", "id": "3_B", "correct": "ethical",
     "wrong": ["financial", "operational", "clinical", "administrative"],
     "difficulty": 0.5},
    {"type": "text", "id": "3_A", "correct": "legal",
     "wrong": ["medical", "ethical", "clinical", "billing"],
     "difficulty": 0.5},
    {"type": "checkbox_multi", "id": "4_A",
     "wrong_ids": ["4_B", "4_C"], "difficulty": 0.4},
    # Q5: correct=FALSE → check "5_T" (visually the F box, field names swapped)
    {"type": "checkbox_pair", "correct_id": "5_T", "wrong_id": "5_F", "difficulty": 0.4},
    {"type": "checkbox_pair", "correct_id": "6_T", "wrong_id": "6_F", "difficulty": 0.3},
    {"type": "checkbox_pair", "correct_id": "7_F", "wrong_id": "7_T", "difficulty": 0.3},
    {"type": "checkbox_pair", "correct_id": "8_T", "wrong_id": "8_F", "difficulty": 0.3},
    {"type": "checkbox_pair", "correct_id": "9_F", "wrong_id": "9_T", "difficulty": 0.3},
    {"type": "checkbox_pair", "correct_id": "10_T", "wrong_id": "10_F", "difficulty": 0.3},
    {"type": "text", "id": "11_A", "correct": "nursing",
     "wrong": ["medical", "hospital", "rehabilitation", "assisted living"],
     "difficulty": 0.4},
    {"type": "text", "id": "11_B", "correct": "institutionalization",
     "wrong": ["hospitalization", "homelessness", "relocation", "deterioration"],
     "difficulty": 0.4},
    {"type": "checkbox_pair", "correct_id": "12_T", "wrong_id": "12_F", "difficulty": 0.3},
    {"type": "text", "id": "13_A", "correct": "Service Coordinator",
     "wrong": ["Case Manager", "Social Worker", "Program Director", "Nurse"],
     "difficulty": 0.4},
    {"type": "checkbox_pair", "correct_id": "14_F", "wrong_id": "14_T", "difficulty": 0},
    {"type": "text", "id": "15_A", "correct": "face-to-face",
     "wrong": ["virtual", "telehealth", "monthly", "weekly", "billable"],
     "difficulty": 0.4},
    {"type": "checkbox_pair", "correct_id": "16\u00ad_T", "wrong_id": "16_F", "difficulty": 0},
]


def generate_correct_fields():
    fields = {}
    for q in ANSWER_KEY:
        if q["type"] == "text":
            fields[q["id"]] = q["correct"]
        elif q["type"] == "checkbox_pair":
            fields[q["correct_id"]] = True
        elif q["type"] == "checkbox_multi":
            fields[q["id"]] = True
    return fields


def generate_pretest_fields():
    wrong_count = 0
    answers = []
    for q in ANSWER_KEY:
        is_wrong = q["difficulty"] > 0 and random.random() < q["difficulty"]
        if is_wrong:
            wrong_count += 1
            if q["type"] == "text":
                answers.append({"q": q, "fid": q["id"],
                               "val": random.choice(q.get("wrong", ["Unsure"]))})
            elif q["type"] == "checkbox_pair":
                answers.append({"q": q, "fid": q["wrong_id"], "val": True})
            elif q["type"] == "checkbox_multi":
                wid = random.choice(q["wrong_ids"])
                answers.append({"q": q, "fid": wid, "val": True})
        else:
            if q["type"] == "text":
                answers.append({"q": q, "fid": q["id"], "val": q["correct"]})
            elif q["type"] == "checkbox_pair":
                answers.append({"q": q, "fid": q["correct_id"], "val": True})
            elif q["type"] == "checkbox_multi":
                answers.append({"q": q, "fid": q["id"], "val": True})

    if wrong_count < 2:
        candidates = [a for a in answers if a["q"]["difficulty"] > 0]
        random.shuffle(candidates)
        for i in range(min(2 - wrong_count, len(candidates))):
            a = candidates[i]
            q = a["q"]
            if q["type"] == "text":
                a["fid"] = q["id"]
                a["val"] = random.choice(q.get("wrong", ["Unsure"]))
            elif q["type"] == "checkbox_pair":
                a["fid"] = q["wrong_id"]
                a["val"] = True
            elif q["type"] == "checkbox_multi":
                wid = random.choice(q["wrong_ids"])
                a["fid"] = wid
                a["val"] = True

    return {a["fid"]: a["val"] for a in answers}


def create_overlay(field_values, staff_name, date_str, pw, ph, page_num, agency="Attentive"):
    """Create a ReportLab overlay with text answers and checkmarks."""
    agency_names = {
        "Attentive": "Attentive Care Service Coordination",
        "Abode": "Abode Care Service Coordination"
    }
    agency_full = agency_names.get(agency, agency)
    
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(pw, ph))

    # Name/date header (page 1 only)
    if page_num == 1:
        y_pos = ph - 78
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(HexColor("#333333"))
        c.drawString(72, y_pos, f"Name: {staff_name}")
        c.drawString(300, y_pos, f"Date: {date_str}")
        c.drawRightString(pw - 72, y_pos, agency_full)

    for fid, val in field_values.items():
        pos = FIELD_POS.get(fid)
        if not pos:
            continue
        cx, cy, w, h, pg = pos
        if pg != page_num:
            continue

        if isinstance(val, bool):
            # Draw a bold X mark inside the box
            c.setStrokeColor(HexColor("#000000"))
            # For tiny checkboxes (<8px), draw a slightly larger mark
            min_size = max(w, h, 8)
            half = min_size / 2 - 1.5
            c.setLineWidth(1.8 if min_size > 7 else 1.2)
            c.line(cx - half, cy - half, cx + half, cy + half)
            c.line(cx - half, cy + half, cx + half, cy - half)
        else:
            # Draw text answer
            c.setFont("Helvetica", 10)
            c.setFillColor(HexColor("#000000"))
            text_x = cx - w/2 + 2
            text_y = cy - 4
            c.drawString(text_x, text_y, str(val))

    c.save()
    return buf.getvalue()


def fill_pdf(field_values, staff_name, date_str, output_path, agency="Attentive"):
    template_path = get_template(agency)
    reader = PdfReader(template_path)
    writer = PdfWriter()

    pw = float(reader.pages[0].mediabox.width)
    ph = float(reader.pages[0].mediabox.height)

    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        # Remove form annotations so they don't cover our overlay
        if "/Annots" in page:
            del page["/Annots"]
        overlay_bytes = create_overlay(field_values, staff_name, date_str, pw, ph, page_num + 1, agency)
        overlay_reader = PdfReader(BytesIO(overlay_bytes))
        page.merge_page(overlay_reader.pages[0])
        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)
    print(f"TEST created: {output_path}")


def generate_tests(staff_name, pre_date, post_date, output_dir, agency="Attentive"):
    os.makedirs(output_dir, exist_ok=True)
    safe_name = staff_name.replace(" ", "_")

    post_fields = generate_correct_fields()
    pre_fields = generate_pretest_fields()

    pre_date_str = pre_date.replace("/", "-")
    post_date_str = post_date.replace("/", "-")

    fill_pdf(post_fields, staff_name, post_date,
             os.path.join(output_dir, f"{safe_name}_Post_Test_{post_date_str}.pdf"), agency)
    fill_pdf(pre_fields, staff_name, pre_date,
             os.path.join(output_dir, f"{safe_name}_Pre_Test_{pre_date_str}.pdf"), agency)


def main():
    if len(sys.argv) < 4:
        print("Usage: python3 generate_tests.py <name> <pre_date> <post_date> [output_dir] [agency]")
        sys.exit(1)

    staff_name = sys.argv[1]
    pre_date = sys.argv[2]
    post_date = sys.argv[3]
    out_dir = sys.argv[4] if len(sys.argv) > 4 else "./output"
    agency = sys.argv[5] if len(sys.argv) > 5 else "Attentive"

    generate_tests(staff_name, pre_date, post_date, out_dir, agency)


if __name__ == "__main__":
    main()
