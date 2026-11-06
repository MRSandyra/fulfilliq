# Local semantic layer

The executable DuckDB definitions live in `src/fulfilliq/exports.py` so the CLI and tests share the same query contract. This directory reserves a location for optional standalone local SQL extracts; it intentionally contains no divergent copy of the business rules.
