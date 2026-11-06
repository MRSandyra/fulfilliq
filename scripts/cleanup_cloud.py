"""Deliberately dry-run-only cleanup guardrail."""

from __future__ import annotations

import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "--confirm",
    help="must exactly equal project id; deletion implementation intentionally requires owner review",
)
parser.add_argument("--project-id", default="fulfilliq")
args = parser.parse_args()
print(
    f"DRY RUN: would inspect only FulfillIQ prefixes raw/, curated/, quarantine/, athena-results/ for project {args.project_id}."
)
if args.confirm == args.project_id:
    raise SystemExit(
        "Deletion is intentionally not automated. Review runbook and perform an explicitly approved, scoped teardown."
    )
