.PHONY: setup lint typecheck test unit local-contract demo-local dashboard reconcile-cloud

setup:
	python -m pip install --upgrade pip
	python -m pip install -r requirements-dev.txt
	python -m pip install -e .
	cd web && npm install

lint:
	python -m ruff check src tests lambda scripts
	python -m ruff format --check src tests lambda scripts

typecheck:
	python -m mypy src/fulfilliq
	cd web && npx tsc -b --pretty false

test:
	python -m pytest tests/unit tests/contract tests/integration tests/ml

unit:
	python -m pytest tests/unit tests/ml

local-contract: demo-local
	python -m pytest tests/contract tests/integration
	cd web && npm run test && npm run build

demo-local:
	python scripts/generate_synthetic_fixtures.py --output data/synthetic
	python -m fulfilliq.cli prepare --source data/synthetic --output data/prepared/synthetic
	python -m fulfilliq.cli replay --input data/prepared/synthetic --output data/batches/synthetic --max-records 100
	python -m fulfilliq.cli local-ingest --input data/batches/synthetic --output data/local-curated/synthetic
	python -m fulfilliq.cli local-query --input data/local-curated/synthetic --output data/exports/synthetic --mode synthetic
	python -m fulfilliq.cli build-dashboard-data --input data/exports/synthetic --output web/public/data --mode synthetic

dashboard:
	cd web && npm run dev

# Requires explicit approval, AWS credentials, FULFILLIQ_BUCKET, and a local
# overview.json generated from the same scoped replay. Example:
# make reconcile-cloud LOCAL_EXPORT=data/exports/olist
reconcile-cloud:
	python -m fulfilliq.cli reconcile-cloud --local $(LOCAL_EXPORT) --evidence artifacts/reports/cloud-reconciliation.json
