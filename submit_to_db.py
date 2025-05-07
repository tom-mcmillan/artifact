#!/usr/bin/env python3
"""
Utility script to submit artifact JSON files into the artifact-db Postgres instance.

Usage:
  submit_to_db.py <file_or_dir> [<file_or_dir> ...]

Each argument may be a path to a JSON file or a directory containing JSON files.
The script will load and validate each artifact JSON for required fields:
  - id
  - created_at
  - content
  - epistemic_trace { justification, diagnostic_flags, detected_by }

Valid artifacts are inserted into the 'artifacts' table using DB credentials from .env.
At the end, a summary report is printed.
"""
import os
import sys
import json
import argparse
from pathlib import Path

import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

REQUIRED_FIELDS = {'id', 'created_at', 'content', 'epistemic_trace'}
TRACE_FIELDS = {'justification', 'diagnostic_flags', 'detected_by'}

def validate_artifact(data):
    missing = REQUIRED_FIELDS - data.keys()
    if missing:
        return False, f"Missing top-level fields: {', '.join(missing)}"
    trace = data.get('epistemic_trace')
    if not isinstance(trace, dict):
        return False, "Field 'epistemic_trace' must be an object"
    missing_trace = TRACE_FIELDS - trace.keys()
    if missing_trace:
        return False, f"Missing trace fields: {', '.join(missing_trace)}"
    return True, None


def gather_files(paths):
    files = []
    for p in paths:
        p = Path(p)
        if p.is_dir():
            files.extend([f for f in p.rglob('*.json') if f.is_file()])
        elif p.is_file() and p.suffix.lower() == '.json':
            files.append(p)
        else:
            print(f"Warning: skipping non-JSON path {p}")
    return files


def load_db_config():
    load_dotenv()
    cfg = {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'dbname': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
    }
    missing = [k for k, v in cfg.items() if not v]
    if missing:
        print(f"Error: missing DB config for: {', '.join(missing)}")
        sys.exit(1)
    return cfg


def main():
    parser = argparse.ArgumentParser(description="Submit artifact JSON files to Postgres DB.")
    parser.add_argument('inputs', nargs='+', help='Paths to JSON files or directories')
    args = parser.parse_args()

    files = gather_files(args.inputs)
    if not files:
        print("No JSON files found to process.")
        sys.exit(0)

    db_cfg = load_db_config()
    conn = psycopg2.connect(**db_cfg)
    cur = conn.cursor()

    success = 0
    failures = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
        except Exception as e:
            failures.append((str(f), f"JSON parse error: {e}"))
            continue

        valid, err = validate_artifact(data)
        if not valid:
            failures.append((str(f), err))
            continue

        try:
            cur.execute(
                """
                INSERT INTO artifacts (knowledge_id, created_at, content, epistemic_trace)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    data['id'],
                    data['created_at'],
                    data['content'],
                    Json(data['epistemic_trace']),
                )
            )
            conn.commit()
            success += 1
        except Exception as e:
            conn.rollback()
            failures.append((str(f), str(e)))

    cur.close()
    conn.close()

    print(f"\nSummary: {success} inserted, {len(failures)} failures.")
    if failures:
        for fpath, reason in failures:
            print(f" - {fpath}: {reason}")


if __name__ == '__main__':
    main()
