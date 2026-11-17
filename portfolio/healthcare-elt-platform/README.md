# Healthcare Operations ELT Platform

Python + SQL portfolio project implementing reliable data ingestion and descriptive operations metrics. Data contracts, SHA-256 batch deduplication, transactional upserts, SQL reporting and a reusable command line interface.

Run from this folder:
```bash
python -m pytest -q tests
python -m healthcare_elt.pipeline --csv examples/synthetic_encounters.csv --db encounters.sqlite --report summary.json
```
Fields: encounter_id, facility, encounter_date (ISO), disposition (admitted/discharged/transferred), wait_minutes (0-1440).
Duplicate IDs in one batch are rejected, identical input batches are safely skipped, revised records are upserted. Reports include mean wait, admission percent and long-wait count by facility.

The example encounters are **synthetic**. This is not patient data, a clinical quality rating, or a deployed production system.

Optional Airflow DAG requires external configuration. Cloud object storage, Snowflake and Terraform are not implemented.
