from fulfilliq.aws_pipeline import planned_uploads


def test_planned_uploads_place_orders_before_outcomes_and_namespace_olist(tmp_path):
    for kind in ("order_placed", "delivery_outcome"):
        directory = tmp_path / kind
        directory.mkdir()
        (directory / "b.jsonl").write_text("{}\n")
        (directory / "a.jsonl").write_text("{}\n")

    plan = planned_uploads(tmp_path, limit_batches=4, run_id="olist-2018-08-31-100")

    assert [key for _, key in plan] == [
        "raw/olist/olist-2018-08-31-100/order_placed/a.jsonl",
        "raw/olist/olist-2018-08-31-100/order_placed/b.jsonl",
        "raw/olist/olist-2018-08-31-100/delivery_outcome/a.jsonl",
        "raw/olist/olist-2018-08-31-100/delivery_outcome/b.jsonl",
    ]


def test_planned_uploads_honors_replay_manifest_order(tmp_path):
    for kind in ("order_placed", "delivery_outcome"):
        directory = tmp_path / kind
        directory.mkdir()
        for batch_id in ("a", "z"):
            (directory / f"{batch_id}.jsonl").write_text("{}\n")
    (tmp_path / "manifest.json").write_text(
        '{"batches":{"order_placed":["z","a"],"delivery_outcome":["z","a"]}}'
    )

    plan = planned_uploads(tmp_path, limit_batches=4, run_id="olist-stage")

    assert [path.name for path, _ in plan] == ["z.jsonl", "a.jsonl", "z.jsonl", "a.jsonl"]
