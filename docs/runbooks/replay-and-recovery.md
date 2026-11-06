# Replay and recovery

Immutable JSONL content determines `batch_id`. A malformed batch is wholly quarantined; no partial curated output is valid. Correct the source data, create a new content hash/batch ID, replay it, and retain the old quarantine report as incident evidence. Repeating the exact same batch is safe: it targets the same deterministic curated key.
