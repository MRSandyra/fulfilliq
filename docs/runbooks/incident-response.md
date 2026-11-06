# Incident response

Record incident ID, first-seen time, batch hashes, scope, redacted failure, containment, root cause, corrected fingerprint, replay steps, verification query, and follow-up. Do not put raw payloads or customer identifiers in logs or evidence. S3 notifications can be duplicate/out of order; investigate using batch IDs rather than treating a retry as a new order.
