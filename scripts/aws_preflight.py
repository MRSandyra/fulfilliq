"""Read-only AWS identity preflight with a CLI fallback for `aws login` sessions."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from datetime import UTC, datetime

import boto3


def redacted_identity(identity: dict) -> dict:
    return {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "account": "REDACTED",
        "identity_type": identity.get("Arn", "").split(":")[-1].split("/")[0],
        "status": "IDENTITY_AVAILABLE",
        "manual_action": (
            "Confirm Free Plan, credits, service eligibility, and region in AWS Console before any apply."
        ),
    }


def cli_identity(cli: str, profile: str | None) -> dict:
    command = [cli, "sts", "get-caller-identity", "--output", "json"]
    if profile:
        command.extend(["--profile", profile])
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


parser = argparse.ArgumentParser(description="Read-only AWS identity preflight")
parser.add_argument("--profile", default=os.getenv("AWS_PROFILE"))
parser.add_argument("--aws-cli", help="optional absolute path to aws.exe")
args = parser.parse_args()

try:
    session = boto3.Session(profile_name=args.profile) if args.profile else boto3.Session()
    print(json.dumps(redacted_identity(session.client("sts").get_caller_identity()), indent=2))
except Exception as boto_error:
    cli = args.aws_cli or os.getenv("AWS_CLI_PATH") or shutil.which("aws")
    if not cli:
        print(
            json.dumps(
                {
                    "checked_at_utc": datetime.now(UTC).isoformat(),
                    "status": "NOT_CHECKED",
                    "reason": f"SDK failed and AWS CLI was not found: {boto_error}",
                },
                indent=2,
            )
        )
    else:
        try:
            print(json.dumps(redacted_identity(cli_identity(cli, args.profile)), indent=2))
        except Exception as cli_error:
            print(
                json.dumps(
                    {
                        "checked_at_utc": datetime.now(UTC).isoformat(),
                        "status": "NOT_CHECKED",
                        "reason": str(cli_error),
                        "manual_action": (
                            "No cloud operation is permitted; record a Console preflight receipt first."
                        ),
                    },
                    indent=2,
                )
            )
