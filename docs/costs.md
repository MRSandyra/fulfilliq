# Cost controls

Cloud replay and Athena reconciliation are **VERIFIED**. The design has no VPC, NAT, EC2, RDS, Redshift, Glue jobs/crawlers, or managed Kafka. The approved full run's three Athena KPI queries scanned 116,627,908 bytes in total, with each query below the 100 MiB workgroup cutoff. A before/after billing balance was not captured, so this is not a zero-cost claim; see `docs/evidence/cost-checks.md`.
