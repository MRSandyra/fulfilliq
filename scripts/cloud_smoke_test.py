"""Bounded cloud smoke guard. Does not upload or query without explicit approval."""

from __future__ import annotations

import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument("--check", required=True)
parser.add_argument("--timeout-seconds", type=int, default=180)
args = parser.parse_args()
if args.check != "upload-lambda-s3-athena":
    raise SystemExit("Only upload-lambda-s3-athena is supported.")
if os.getenv("ALLOW_CLOUD_DEPLOY") != "true":
    raise SystemExit("CLOUD NOT VERIFIED: owner approval flag is absent; no AWS call was made.")
raise SystemExit(
    "Manual evidence required: upload a fresh approved synthetic batch, then record curated key, Lambda log, Athena query ID, and cost receipt."
)
