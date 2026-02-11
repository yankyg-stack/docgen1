#!/usr/bin/env python3
"""
Master orchestration: generates ALL documents for ALL staff.
Input JSON: [{"name":"Jane Doe","startDate":"2021-06-15","endDate":"","agency":"Attentive"}, ...]
"""
import sys, os, json, subprocess, shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_BASE = os.path.join(SCRIPT_DIR, "output")


def process_staff(staff):
    name = staff["name"]
    start = staff["startDate"]
    end = staff.get("endDate", "") or ""
    agency = staff.get("agency", "Attentive")
    safe_name = name.replace(" ", "_")
    out_dir = os.path.join(OUTPUT_BASE, safe_name)

    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Processing: {name} ({agency})")
    print(f"  Start: {start}  |  End: {end or 'still employed'}")
    print(f"{'='*60}")

    # Step 1: Generate training log
    cmd_log = ["node", os.path.join(SCRIPT_DIR, "generate_log.js"),
               name, start, end, out_dir, agency]
    result = subprocess.run(cmd_log, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"ERROR generating log: {result.stderr}")
        return False

    # Step 2: Generate certificates
    rows_json = os.path.join(out_dir, f"{safe_name}_rows.json")
    cmd_cert = ["python3", os.path.join(SCRIPT_DIR, "generate_certs.py"),
                name, rows_json, out_dir, agency]
    result = subprocess.run(cmd_cert, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"ERROR generating certs: {result.stderr}")
        return False

    # Step 3: Generate pre-test and post-test (first year only)
    with open(rows_json) as f:
        rows = json.load(f)
    if rows:
        pre_date = rows[0]["trainingDate"]
        post_date = rows[0]["certDate"]
        cmd_test = ["python3", os.path.join(SCRIPT_DIR, "generate_tests.py"),
                    name, pre_date, post_date, out_dir, agency]
        result = subprocess.run(cmd_test, capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(f"ERROR generating tests: {result.stderr}")

    os.remove(rows_json)

    files = sorted(os.listdir(out_dir))
    print(f"\n  Generated {len(files)} files:")
    for f in files:
        size = os.path.getsize(os.path.join(out_dir, f))
        print(f"    - {f} ({size:,} bytes)")
    return True


def main():
    if len(sys.argv) < 2:
        staff_list = [
            {"name": "Jane Doe", "startDate": "2021-06-15", "agency": "Attentive"},
            {"name": "John Smith", "startDate": "2022-11-03", "agency": "Abode"},
        ]
        print("No input — running demo...")
    else:
        staff_list = json.loads(sys.argv[1])

    os.makedirs(OUTPUT_BASE, exist_ok=True)
    success = failed = 0
    for staff in staff_list:
        if process_staff(staff):
            success += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"DONE: {success} succeeded, {failed} failed out of {len(staff_list)} staff")

    manifest = {}
    for staff in staff_list:
        safe = staff["name"].replace(" ", "_")
        folder = os.path.join(OUTPUT_BASE, safe)
        if os.path.exists(folder):
            manifest[staff["name"]] = {"folder": folder, "files": sorted(os.listdir(folder))}
    with open(os.path.join(OUTPUT_BASE, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)


if __name__ == "__main__":
    main()
