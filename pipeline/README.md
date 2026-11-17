# Neonatal Outcome Analytics Pipeline

A tested Python and SQL data pipeline for aggregated neonatal outcome data, extending the existing CDC WONDER / SQL Server work.

## Features
- Validates all CSV cohort records before updating the database.
- Stores records in SQLite with primary-key and check constraints.
- Computes birth-weighted low-birth-weight and preterm rates and mean birth weight.
- Exports yearly, group-level, and overall KPIs to JSON.
- Includes 10 Python unittest regression tests; no third-party dependencies.

## Run (Python 3.10+)
From the repository root on macOS/Linux:
```bash
PYTHONPATH=pipeline/src python -m unittest discover -s pipeline/tests -v
PYTHONPATH=pipeline/src python -m neonatal_pipeline.cli --input pipeline/data/synthetic_cohorts.csv --database neonatal.sqlite --output neonatal_report.json
```
On Windows PowerShell:
```powershell
$env:PYTHONPATH = 'pipeline/src'
python -m unittest discover -s pipeline/tests -v
python -m neonatal_pipeline.cli --input pipeline/data/synthetic_cohorts.csv --database neonatal.sqlite --output neonatal_report.json
```

## Input
Required columns: year, group_name, births, low_birth_weight_births, preterm_births, birth_weight_grams_sum.
Records represent mutually exclusive year/group cohorts. Outcome counts cannot exceed births. Birth-weight grams sum is the total weight across all births, not an average.

**The bundled dataset is fabricated demonstration data, not CDC data.** Do not interpret demo results as real neonatal health trends. Real CDC tables require careful transformations and handling of suppression and subgroup denominators.

## KPI formulas
- Low birth weight rate (%) = 100 * SUM(low_birth_weight_births) / SUM(births)
- Preterm rate (%) = 100 * SUM(preterm_births) / SUM(births)
- Mean birth weight (g) = SUM(birth_weight_grams_sum) / SUM(births)

## Engineering decisions
All rows are validated before dataset replacement. SQL check constraints and composite primary keys add safeguards. Only predefined grouping fields are permitted. Reported metrics are descriptive statistics, not medical conclusions.

## Planned follow-up
Integrate the existing CDC WONDER exports using a documented transformation and publish dashboard visualizations.
