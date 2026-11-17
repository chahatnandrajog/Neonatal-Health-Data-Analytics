"""Validated ingestion and birth-weighted neonatal outcome analytics."""
from __future__ import annotations
import csv
import json
import sqlite3
from pathlib import Path

REQUIRED = ("year", "group_name", "births", "low_birth_weight_births", "preterm_births", "birth_weight_grams_sum")
SCHEMA = """CREATE TABLE IF NOT EXISTS cohorts (
    year INTEGER NOT NULL,
    group_name TEXT NOT NULL,
    births INTEGER NOT NULL CHECK (births > 0),
    low_birth_weight_births INTEGER NOT NULL CHECK (low_birth_weight_births BETWEEN 0 AND births),
    preterm_births INTEGER NOT NULL CHECK (preterm_births BETWEEN 0 AND births),
    birth_weight_grams_sum INTEGER NOT NULL CHECK (birth_weight_grams_sum BETWEEN births * 300 AND births * 7000),
    PRIMARY KEY (year, group_name)
)"""

def _integer(value: str, field: str, row_number: int) -> int:
    try:
        return int(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"row {row_number}: {field} must be an integer") from exc

def read_cohorts(csv_path: str | Path) -> list[tuple[int, str, int, int, int, int]]:
    """Validate all rows before any DB mutation."""
    output = []
    seen = set()
    with open(csv_path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not set(REQUIRED).issubset(reader.fieldnames):
            raise ValueError(f"CSV must contain columns: {', '.join(REQUIRED)}")
        for n, row in enumerate(reader, 2):
            year = _integer(row["year"], "year", n)
            group = (row["group_name"] or "").strip()
            births, lbw, preterm, weight = (
                _integer(row[key], key, n) for key in REQUIRED[2:]
            )
            if not 1900 <= year <= 2100:
                raise ValueError(f"row {n}: year outside supported range")
            if not group:
                raise ValueError(f"row {n}: group_name cannot be empty")
            if (year, group) in seen:
                raise ValueError(f"row {n}: duplicate year/group_name")
            if births <= 0 or min(lbw, preterm) < 0 or max(lbw, preterm) > births:
                raise ValueError(f"row {n}: impossible outcome counts")
            if not 300 * births <= weight <= 7000 * births:
                raise ValueError(f"row {n}: implausible aggregate birth weight")
            seen.add((year, group))
            output.append((year, group, births, lbw, preterm, weight))
    if not output:
        raise ValueError("CSV has no cohort records")
    return output

def ingest(csv_path: str | Path, db_path: str | Path) -> int:
    """Replace database rows only after the complete input validates."""
    records = read_cohorts(csv_path)
    with sqlite3.connect(db_path) as connection:
        connection.execute(SCHEMA)
        with connection:
            connection.execute("DELETE FROM cohorts")
            connection.executemany("INSERT INTO cohorts VALUES (?, ?, ?, ?, ?, ?)", records)
    return len(records)

def aggregate(db_path: str | Path, by: str = "year") -> list[dict]:
    dimensions = {"year": "year", "group": "group_name", "overall": "'all'"}
    if by not in dimensions:
        raise ValueError("by must be year, group, or overall")
    dimension = dimensions[by]
    sql = f"""SELECT {dimension} AS cohort,
        SUM(births) AS births,
        SUM(low_birth_weight_births) AS low_birth_weight_births,
        SUM(preterm_births) AS preterm_births,
        SUM(birth_weight_grams_sum) AS total_birth_weight_grams
        FROM cohorts GROUP BY {dimension} ORDER BY {dimension}"""
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        records = [dict(row) for row in connection.execute(sql)]
    for row in records:
        b = row["births"]
        row["low_birth_weight_rate_pct"] = round(100 * row["low_birth_weight_births"] / b, 2)
        row["preterm_rate_pct"] = round(100 * row["preterm_births"] / b, 2)
        row["mean_birth_weight_grams"] = round(row.pop("total_birth_weight_grams") / b, 2)
    return records

def export_json(db_path: str | Path, output_path: str | Path) -> None:
    data = {"overall": aggregate(db_path, "overall"),
            "annual": aggregate(db_path, "year"),
            "by_group": aggregate(db_path, "group")}
    Path(output_path).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
