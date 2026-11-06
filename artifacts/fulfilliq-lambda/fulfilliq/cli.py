from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import athena, aws_pipeline, datasets, exports, local_pipeline, replay
from .ml.score import score_aggregate
from .ml.train import train_from_facts


def path(value: str) -> Path:
    return Path(value)


def _print(value: object) -> None:
    print(json.dumps(value, indent=2, default=str))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fulfilliq", description="FulfillIQ local-first delivery SLA workflow"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def command(name: str):
        return sub.add_parser(name)

    p = command("validate-source")
    p.add_argument("--source", type=path, required=True)
    p = command("prepare")
    p.add_argument("--source", type=path, required=True)
    p.add_argument("--output", type=path, required=True)
    p = command("replay")
    p.add_argument("--input", type=path, required=True)
    p.add_argument("--output", type=path, required=True)
    p.add_argument("--as-of")
    p.add_argument("--max-records", type=int, default=100)
    p.add_argument("--max-bytes", type=int, default=256 * 1024)
    p.add_argument("--order-limit", type=int)
    p = command("local-ingest")
    p.add_argument("--input", type=path, required=True)
    p.add_argument("--output", type=path, required=True)
    p = command("local-query")
    p.add_argument("--input", type=path, required=True)
    p.add_argument("--output", type=path, required=True)
    p.add_argument("--mode", choices=["synthetic", "local"], default="local")
    p = command("build-dashboard-data")
    p.add_argument("--input", type=path, required=True)
    p.add_argument("--output", type=path, required=True)
    p.add_argument("--mode", choices=["synthetic", "local"], default="local")
    p = command("upload-events")
    p.add_argument("--source", type=path, required=True)
    p.add_argument("--mode", choices=["dry-run", "apply"], required=True)
    p.add_argument("--limit-batches", type=int, default=5)
    p.add_argument("--run-id")
    p = command("train")
    p.add_argument("--input", type=path, required=True)
    p.add_argument("--output", type=path, required=True)
    p = command("score")
    p.add_argument("--model", type=path, required=True)
    p.add_argument("--input", type=path, required=True)
    p.add_argument("--output", type=path, required=True)
    p = command("compare-warehouse")
    p.add_argument("--local", type=path, required=True)
    p.add_argument("--cloud", type=path, required=True)
    p = command("export-athena")
    p.add_argument("--output", type=path, required=True)
    p.add_argument("--limit-queries", type=int, default=10)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "validate-source":
        _print(datasets.validate_source(args.source))
    elif args.command == "prepare":
        _print(datasets.prepare(args.source, args.output))
    elif args.command == "replay":
        _print(
            replay.create_batches(
                args.input,
                args.output,
                as_of=args.as_of,
                max_records=args.max_records,
                max_bytes=args.max_bytes,
                order_limit=args.order_limit,
            )
        )
    elif args.command == "local-ingest":
        _print(local_pipeline.ingest_batches(args.input, args.output))
    elif args.command == "local-query":
        _print(exports.export_local(args.input, args.output, mode=args.mode))
    elif args.command == "build-dashboard-data":
        exports.copy_dashboard_data(args.input, args.output, mode=args.mode)
    elif args.command == "upload-events":
        _print(
            {
                "keys": aws_pipeline.upload_events(
                    args.source,
                    mode=args.mode,
                    limit_batches=args.limit_batches,
                    run_id=args.run_id,
                )
            }
        )
    elif args.command == "train":
        _print(train_from_facts(args.input / "facts.jsonl", args.output))
    elif args.command == "score":
        _print(score_aggregate(args.model, args.input, args.output))
    elif args.command == "compare-warehouse":
        local = json.loads((args.local / "overview.json").read_text(encoding="utf-8"))
        cloud = json.loads((args.cloud / "overview.json").read_text(encoding="utf-8"))
        differences = {
            key: {"local": local.get(key), "cloud": cloud.get(key)}
            for key in set(local) | set(cloud)
            if local.get(key) != cloud.get(key)
        }
        _print({"matches": not differences, "differences": differences})
    elif args.command == "export-athena":
        if args.limit_queries < 3:
            raise ValueError("export-athena requires at least three bounded read queries")
        overview_id, overview_rows = athena.query_rows(
            "SELECT count(*) AS total_orders, sum(eligible_delivery) AS eligible_delivered_orders, "
            "sum(delivery_late) AS late_delivered_orders, "
            "sum(delivery_late) * 1.0 / nullif(sum(eligible_delivery),0) AS late_delivery_rate, "
            "sum(order_value_brl) AS gmv_brl, count(*)-sum(eligible_delivery) AS undelivered_orders "
            "FROM fulfilliq.v_order_delivery"
        )
        daily_id, daily = athena.query_rows(
            "SELECT * FROM fulfilliq.v_daily_sla ORDER BY purchase_date"
        )
        regions_id, regions = athena.query_rows(
            "SELECT customer_state, count(*) AS orders_placed, sum(eligible_delivery) AS eligible_delivered_orders, "
            "sum(delivery_late) AS late_delivered_orders, sum(delivery_late) * 1.0 / nullif(sum(eligible_delivery),0) AS late_delivery_rate "
            "FROM fulfilliq.v_order_delivery GROUP BY customer_state"
        )
        args.output.mkdir(parents=True, exist_ok=True)
        for name, value in {
            "overview.json": overview_rows[0],
            "sla_daily.json": daily,
            "sla_regions.json": regions,
        }.items():
            (args.output / name).write_text(json.dumps(value, indent=2), encoding="utf-8")
        _print({"query_execution_ids": [overview_id, daily_id, regions_id], "status": "EXPORTED"})


if __name__ == "__main__":
    main()
