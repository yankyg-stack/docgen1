#!/usr/bin/env python3
"""
Master orchestration script: generates ALL documents for ALL staff.

Usage:
  python3 process_all_staff.py '<JSON array of staff>'

  JSON format:
  [
    {"name": "Jane Doe",  "startDate": "2021-06-15"},
    {"name": "John Smith", "startDate": "2019-01-10", "endDate": "2023-05-01"}
  ]

Output structure:
  ./output/
    Jane_Doe/
      Jane_Doe_Training_Log.docx
      Jane_Doe_Certificate_06-17-2021.pdf
      Jane_Doe_Certificate_06-10-2022.pdf
      ...
    John_Smith/
      ...
"""
import sys
import os
import json
import subprocess
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_BASE = os.path.join(SCRIPT_DIR, "output")


def process_staff(staff):
    name = staff["name"]
    start = staff["startDate"]
    end = staff.get("endDate", "")
    safe_name = name.replace(" ", "_")
    out_dir = os.path.join(OUTPUT_BASE, safe_name)

    # Clean previous output
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Processing: {name}")
    print(f"  Start: {start}  |  End: {end or 'still employed'}")
    print(f"  Output: {out_dir}")
    print(f"{'='*60}")

    # Step 1: Generate training log + row data
    cmd_log = [
        "node", os.path.join(SCRIPT_DIR, "generate_log.js"),
        name, start, end, out_dir
    ]
    result = subprocess.run(cmd_log, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"ERROR generating log: {result.stderr}")
        return False

    # Step 2: Generate certificates
    rows_json = os.path.join(out_dir, f"{safe_name}_rows.json")
    cmd_cert = [
        "python3", os.path.join(SCRIPT_DIR, "generate_certs.py"),
        name, rows_json, out_dir
    ]
    result = subprocess.run(cmd_cert, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"ERROR generating certs: {result.stderr}")
        return False

    # Step 3: Generate pre-test and post-test (only for the FIRST year / hire date)
    with open(rows_json) as f:
        rows = json.load(f)
    if rows:
        pre_date = rows[0]["trainingDate"]   # hire date
        post_date = rows[0]["certDate"]       # hire date + 2 days
        cmd_test = [
            "python3", os.path.join(SCRIPT_DIR, "generate_tests.py"),
            name, pre_date, post_date, out_dir
        ]
        result = subprocess.run(cmd_test, capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(f"ERROR generating tests: {result.stderr}")

    # Clean up the intermediate rows JSON
    os.remove(rows_json)

    # List all generated files
    files = sorted(os.listdir(out_dir))
    print(f"\n  Generated {len(files)} files:")
    for f in files:
        size = os.path.getsize(os.path.join(out_dir, f))
        print(f"    - {f} ({size:,} bytes)")

    return True


def main():
    if len(sys.argv) < 2:
        # Demo mode with sample data
        staff_list = [
            {"name": "Jane Doe",   "startDate": "2021-06-15"},
            {"name": "John Smith", "startDate": "2019-01-10", "endDate": "2023-05-01"},
        ]
        print("No input provided — running demo with sample data...")
    else:
        staff_list = json.loads(sys.argv[1])

    os.makedirs(OUTPUT_BASE, exist_ok=True)

    success = 0
    failed = 0
    for staff in staff_list:
        if process_staff(staff):
            success += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"DONE: {success} succeeded, {failed} failed out of {len(staff_list)} staff")
    print(f"Output directory: {OUTPUT_BASE}")

    # Output a manifest (useful for N8N to know what files were created)
    manifest = {}
    for staff in staff_list:
        safe = staff["name"].replace(" ", "_")
        folder = os.path.join(OUTPUT_BASE, safe)
        if os.path.exists(folder):
            manifest[staff["name"]] = {
                "folder": folder,
                "files": sorted(os.listdir(folder))
            }
    manifest_path = os.path.join(OUTPUT_BASE, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
