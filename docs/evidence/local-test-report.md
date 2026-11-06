# Local test report

Run: 2026-11-06 UTC, Python 3.12.16.

- `ruff check src tests`: passed.
- `ruff format --check src tests`: passed.
- `pytest tests/unit tests/contract tests/integration tests/ml --basetemp .pytest-tmp`: **6 passed** in 1.56 seconds.
- Web `npm run lint`: passed.
- Web `npm run test`: **1 passed**.
- Web `npm run build`: passed (Vite static bundle produced).

The initial default pytest temporary location was inaccessible to the sandbox, so the successful run used a workspace-local `--basetemp`. This is an environment path constraint, not a suppressed test failure.
