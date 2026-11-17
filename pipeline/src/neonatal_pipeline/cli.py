"""Command-line interface for the neonatal analytics pipeline."""
import argparse
from .core import ingest, export_json

def main():
    p = argparse.ArgumentParser(description="Validate cohort CSV and compute neonatal outcome KPIs")
    p.add_argument("--input", required=True)
    p.add_argument("--database", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    count = ingest(args.input, args.database)
    export_json(args.database, args.output)
    print(f"Validated {count} cohorts; KPI report written to {args.output}")

if __name__ == "__main__":
    main()
