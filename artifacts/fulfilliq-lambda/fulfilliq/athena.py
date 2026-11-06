from __future__ import annotations

import os
import time
from pathlib import Path

import boto3


def require_approved_cloud() -> tuple[object, str, str]:
    if os.getenv("ALLOW_CLOUD_DEPLOY") != "true":
        raise PermissionError(
            "cloud action blocked; owner approval flag ALLOW_CLOUD_DEPLOY=true is required"
        )
    bucket = os.getenv("FULFILLIQ_BUCKET")
    if not bucket:
        raise ValueError("FULFILLIQ_BUCKET is required")
    region = os.getenv("AWS_REGION", "ap-southeast-1")
    return boto3.client("athena", region_name=region), bucket, region


def run_sql(sql: str, *, workgroup: str = "fulfilliq-workgroup") -> str:
    client, bucket, _ = require_approved_cloud()
    response = client.start_query_execution(
        QueryString=sql,
        WorkGroup=workgroup,
        ResultConfiguration={"OutputLocation": f"s3://{bucket}/athena-results/"},
    )
    execution_id = response["QueryExecutionId"]
    while True:
        status = client.get_query_execution(QueryExecutionId=execution_id)["QueryExecution"][
            "Status"
        ]
        state = status["State"]
        if state == "SUCCEEDED":
            return execution_id
        if state in {"FAILED", "CANCELLED"}:
            raise RuntimeError(
                f"Athena {state}: {status.get('StateChangeReason', 'no reason')}; id={execution_id}"
            )
        time.sleep(1)


def query_rows(
    sql: str, *, workgroup: str = "fulfilliq-workgroup"
) -> tuple[str, list[dict[str, str | None]]]:
    """Execute an approved Athena read query and return JSON-safe rows with its execution ID."""
    execution_id = run_sql(sql, workgroup=workgroup)
    client, _, _ = require_approved_cloud()
    result = client.get_query_results(QueryExecutionId=execution_id)["ResultSet"]
    headers = [item["VarCharValue"] for item in result["ResultSetMetadata"]["ColumnInfo"]]
    rows = []
    for row in result["Rows"][1:]:
        values = [cell.get("VarCharValue") for cell in row["Data"]]
        rows.append(dict(zip(headers, values, strict=False)))
    return execution_id, rows


def ddl_files(sql_dir: Path, bucket: str) -> list[str]:
    return [
        path.read_text(encoding="utf-8").replace("<approved-bucket>", bucket)
        for path in sorted(sql_dir.glob("*.sql"))
    ]
