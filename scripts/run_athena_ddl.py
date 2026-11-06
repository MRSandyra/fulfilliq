"""Run reviewed Athena DDL only when the owner has enabled the cloud guard."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from fulfilliq.athena import ddl_files, run_sql

parser = argparse.ArgumentParser()
parser.add_argument("--apply", action="store_true")
parser.add_argument("--dry-run", action="store_true", help="print intent without AWS calls")
parser.add_argument("--sql-dir", type=Path, default=Path("sql"))
parser.add_argument("--workgroup", default="fulfilliq-workgroup")
args = parser.parse_args()
bucket = os.getenv("FULFILLIQ_BUCKET", "<approved-bucket>")
statements = ddl_files(args.sql_dir, bucket)
if args.dry_run and args.apply:
    raise SystemExit("Choose only one of --dry-run or --apply.")
if not args.apply:
    print(
        f"DRY RUN: would execute {len(statements)} reviewed Athena statements using bucket {bucket}."
    )
elif os.getenv("ALLOW_CLOUD_DEPLOY") != "true":
    raise SystemExit("Blocked: ALLOW_CLOUD_DEPLOY=true is required after explicit owner approval.")
else:
    for statement in statements:
        print(run_sql(statement, workgroup=args.workgroup))
