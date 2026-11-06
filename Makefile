.PHONY: setup lint test demo-local dashboard

setup:
	python -m pip install --upgrade pip
	python -m pip install -r requirements-dev.txt
	cd web && npm install

lint:
	python -m ruff check src tests
	python -m ruff format --check src tests

test:
	python -m pytest tests/unit tests/contract tests/integration tests/ml

demo-local:
	python scripts/generate_synthetic_fixtures.py --output data/synthetic
	python -m fulfilliq.cli prepare --source data/synthetic --output data/prepared/synthetic
	python -m fulfilliq.cli replay --input data/prepared/synthetic --output data/batches/synthetic --max-records 100
	python -m fulfilliq.cli local-ingest --input data/batches/synthetic --output data/local-curated/synthetic
	python -m fulfilliq.cli local-query --input data/local-curated/synthetic --output data/exports/synthetic --mode synthetic
	python -m fulfilliq.cli build-dashboard-data --input data/exports/synthetic --output web/public/data --mode synthetic

dashboard:
	cd web && npm run dev
