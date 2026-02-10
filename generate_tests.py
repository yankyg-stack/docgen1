#!/usr/bin/env python3
"""
Generate pre-test and post-test PDFs by filling the SC_Testing_Attentive_Final.pdf form.
Pre-test: realistic random mistakes (at least 2 wrong).
Post-test: 100% correct answers.
Name/Date overlaid via reportlab (no form fields for those in the template).
"""
import sys
import os
import random
from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

TEMPLATE_PDF = os.environ.get(
    "TEMPLATE_PDF_TEST",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "SC_Testing_Attentive_Final.pdf")
)

PAGE1_FIELDS = {"1_A","1_B","2_T","2_F","3_A","3_B","4_A","4_B","4_C",
                "5_T","5_F","6_T","6_F","7_T","7_F","8_T","8_F"}

CHECKED_VALUES = {
    "2_T": "/On", "2_F": "/On",
    "4_A": "/Yes", "4_B": "/Yes", "4_C": "/Yes",
    "5_T": "/Yes", "5_F": "/Yes",
    "6_T": "/Yes", "6_F": "/Yes",
    "7_T": "/Yes", "7_F": "/Yes",
    "8_T": "/Yes", "8_F": "/Yes",
    "9_T": "/Yes", "9_F": "/Yes",
    "10_T": "/Yes", "10_F": "/Yes",
    "12_T": "/Yes", "12_F": "/Yes",
    "14_T": "/Yes", "14_F": "/Yes",
    "16\u00ad_T": "/Yes", "16_F": "/Yes",
}

ANSWER_KEY = [
    {"type": "text", "id": "1_A", "correct": "regulatory risk",
     "wrong": ["patient dissatisfaction", "loss", "problems", "growth",
               "missing agency profits", "inefficient staffing schedules", "redundant overhead costs"],
     "difficulty": 0.5},
    {"type": "text", "id": "1_B", "correct": "non-compliance",
     "wrong": ["losing money", "lawsuits", "fraud", "danger",
               "bankruptcy", "being fired", "delayed payments"],
     "difficulty": 0.5},
    {"type": "checkbox_pair", "correct_id": "2_T", "wrong_id": "2_F", "difficulty": 0},
    {"type": "text", "id": "3_B", "correct": "ethical",
     "wrong": ["financial", "legal", "correct", "proper", "official", "nice", "good", "corporate"],
     "difficulty": 0.3},
    {"type": "text", "id": "3_A", "correct": "legal",
     "wrong": ["moral", "social", "high", "kosher", "raised", "ethical"],
     "difficulty": 0.3},
    {"type": "checkbox_multi", "id": "4_A", "wrong_ids": ["4_B", "4_C"], "difficulty": 0.3},
    {"type": "checkbox_pair", "correct_id": "5_F", "wrong_id": "5_T", "difficulty": 0.4},
    {"type": "checkbox_pair", "correct_id": "6_T", "wrong_id": "6_F", "difficulty": 0},
    {"type": "checkbox_pair", "correct_id": "7_F", "wrong_id": "7_T", "difficulty": 0},
    {"type": "checkbox_pair", "correct_id": "8_T", "wrong_id": "8_F", "difficulty": 0},
    {"type": "checkbox_pair", "correct_id": "9_F", "wrong_id": "9_T", "difficulty": 0.3},
    {"type": "checkbox_pair", "correct_id": "10_T", "wrong_id": "10_F", "difficulty": 0.3},
    {"type": "text", "id": "11_A", "correct": "nursing",
     "wrong": ["hospital", "rehab", "mental", "inpatient", "psychiatric", "assisted living", "home"],
     "difficulty": 0.5},
    {"type": "text", "id": "11_B", "correct": "institutionalization",
     "wrong": ["sickness", "poverty", "incarceration", "loss of coverage", "injury", "risks", "medication"],
     "difficulty": 0.5},
    {"type": "checkbox_pair", "correct_id": "12_T", "wrong_id": "12_F", "difficulty": 0.3},
    {"type": "text", "id": "13_A", "correct": "Service Coordinator",
     "wrong": ["case manager", "social worker", "intake representative", "employee",
               "intake worker", "applicant's relatives", "nurse"],
     "difficulty": 0.4},
    {"type": "checkbox_pair", "correct_id": "14_F", "wrong_id": "14_T", "difficulty": 0},
    {"type": "text", "id": "15_A", "correct": "face-to-face",
     "wrong": ["virtual", "telehealth", "and every", "individual", "billable", "approved", "monthly", "weekly"],
     "difficulty": 0.4},
    {"type": "checkbox_pair", "correct_id": "16\u00ad_T", "wrong_id": "16_F", "difficulty": 0},
]


def generate_correct_fields():
    fields = {}
    for q in ANSWER_KEY:
        if q["type"] == "text":
            fields[q["id"]] = q["correct"]
        elif q["type"] == "checkbox_pair":
            fields[q["correct_id"]] = CHECKED_VALUES.get(q["correct_id"], "/Yes")
        elif q["type"] == "checkbox_multi":
            fields[q["id"]] = CHECKED_VALUES.get(q["id"], "/Yes")
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
                               "val": random.choice(q.get("wrong", ["Unsure"])), "wrong": True})
            elif q["type"] == "checkbox_pair":
                answers.append({"q": q, "fid": q["wrong_id"],
                               "val": CHECKED_VALUES.get(q["wrong_id"], "/Yes"), "wrong": True})
            elif q["type"] == "checkbox_multi":
                wid = random.choice(q["wrong_ids"])
                answers.append({"q": q, "fid": wid,
                               "val": CHECKED_VALUES.get(wid, "/Yes"), "wrong": True})
        else:
            if q["type"] == "text":
                answers.append({"q": q, "fid": q["id"], "val": q["correct"], "wrong": False})
            elif q["type"] == "checkbox_pair":
                answers.append({"q": q, "fid": q["correct_id"],
                               "val": CHECKED_VALUES.get(q["correct_id"], "/Yes"), "wrong": False})
            elif q["type"] == "checkbox_multi":
                answers.append({"q": q, "fid": q["id"],
                               "val": CHECKED_VALUES.get(q["id"], "/Yes"), "wrong": False})

    if wrong_count < 2:
        candidates = [a for a in answers if not a["wrong"] and a["q"]["difficulty"] > 0]
        random.shuffle(candidates)
        for i in range(min(2 - wrong_count, len(candidates))):
            a = candidates[i]
            q = a["q"]
            a["wrong"] = True
            if q["type"] == "text":
                a["fid"] = q["id"]
                a["val"] = random.choice(q.get("wrong", ["Unsure"]))
            elif q["type"] == "checkbox_pair":
                a["fid"] = q["wrong_id"]
                a["val"] = CHECKED_VALUES.get(q["wrong_id"], "/Yes")
            elif q["type"] == "checkbox_multi":
                wid = random.choice(q["wrong_ids"])
                a["fid"] = wid
                a["val"] = CHECKED_VALUES.get(wid, "/Yes")

    return {a["fid"]: a["val"] for a in answers}


def create_name_date_overlay(staff_name, date_str, pw, ph):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(pw, ph))
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(HexColor("#000000"))
    c.drawString(72, ph - 50, f"Name: {staff_name}")
    c.drawString(350, ph - 50, f"Date: {date_str}")
    c.save()
    return buf.getvalue()


def fill_pdf(field_values, staff_name, date_str, output_path):
    reader = PdfReader(TEMPLATE_PDF)
    writer = PdfWriter()
    writer.append(reader)

    page1_vals = {k: v for k, v in field_values.items() if k in PAGE1_FIELDS}
    page2_vals = {k: v for k, v in field_values.items() if k not in PAGE1_FIELDS}

    if page1_vals:
        writer.update_page_form_field_values(writer.pages[0], page1_vals, auto_regenerate=False)
    if page2_vals:
        writer.update_page_form_field_values(writer.pages[1], page2_vals, auto_regenerate=False)

    p0 = reader.pages[0]
    pw = float(p0.mediabox.width)
    ph = float(p0.mediabox.height)
    overlay_bytes = create_name_date_overlay(staff_name, date_str, pw, ph)
    overlay_reader = PdfReader(BytesIO(overlay_bytes))
    writer.pages[0].merge_page(overlay_reader.pages[0])

    with open(output_path, "wb") as f:
        writer.write(f)
    print(f"TEST created: {output_path}")


def generate_tests(staff_name, pre_date, post_date, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    safe_name = staff_name.replace(" ", "_")

    post_fields = generate_correct_fields()
    post_path = os.path.join(output_dir, f"{safe_name}_Post_Test_{post_date.replace('/', '-')}.pdf")
    fill_pdf(post_fields, staff_name, post_date, post_path)

    pre_fields = generate_pretest_fields()
    pre_path = os.path.join(output_dir, f"{safe_name}_Pre_Test_{pre_date.replace('/', '-')}.pdf")
    fill_pdf(pre_fields, staff_name, pre_date, pre_path)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 generate_tests.py <staff_name> <pre_date> <post_date> [output_dir]")
        sys.exit(1)

    generate_tests(sys.argv[1], sys.argv[2], sys.argv[3],
                   sys.argv[4] if len(sys.argv) > 4 else "./output")
