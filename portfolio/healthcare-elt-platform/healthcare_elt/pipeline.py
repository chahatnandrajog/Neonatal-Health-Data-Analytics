"""Validated healthcare operations ELT with deterministic SQL reports."""
import argparse,csv,hashlib,json,sqlite3
from datetime import date
from pathlib import Path

FIELDS=("encounter_id","facility","encounter_date","disposition","wait_minutes")
SCHEMA="""
CREATE TABLE IF NOT EXISTS import_batches(
file_hash TEXT PRIMARY KEY,loaded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,row_count INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS encounters(
encounter_id TEXT PRIMARY KEY,facility TEXT NOT NULL,encounter_date TEXT NOT NULL,
disposition TEXT NOT NULL CHECK(disposition IN ('admitted','discharged','transferred')),
wait_minutes INTEGER NOT NULL CHECK(wait_minutes BETWEEN 0 AND 1440));
"""
def validate_file(path):
    records=[];seen=set()
    with open(path,newline="",encoding="utf-8-sig") as handle:
        reader=csv.DictReader(handle)
        if not reader.fieldnames or not set(FIELDS).issubset(reader.fieldnames):
            raise ValueError("Missing required input columns")
        for n,row in enumerate(reader,2):
            ident=(row["encounter_id"] or "").strip()
            facility=(row["facility"] or "").strip()
            status=(row["disposition"] or "").strip().lower()
            if not ident or not facility:raise ValueError(f"row {n}: missing identifier or facility")
            if ident in seen:raise ValueError(f"row {n}: duplicate encounter_id")
            seen.add(ident)
            try:day=date.fromisoformat(row["encounter_date"])
            except (TypeError,ValueError) as exc:raise ValueError(f"row {n}: invalid date") from exc
            if status not in ("admitted","discharged","transferred"):
                raise ValueError(f"row {n}: invalid disposition")
            try:wait=int(row["wait_minutes"])
            except (TypeError,ValueError) as exc:raise ValueError(f"row {n}: wait_minutes must be integer") from exc
            if not 0<=wait<=1440:raise ValueError(f"row {n}: wait_minutes out of range")
            records.append((ident,facility,day.isoformat(),status,wait))
    if not records:raise ValueError("No encounter data")
    return records

def load_file(path,db_path):
    digest=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    records=validate_file(path)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)
        conn.execute("BEGIN")
        try:
            if conn.execute("SELECT 1 FROM import_batches WHERE file_hash=?",(digest,)).fetchone():
                conn.rollback()
                return {"loaded":0,"already_processed":True,"sha256":digest}
            conn.executemany("""INSERT INTO encounters VALUES(?,?,?,?,?)
                ON CONFLICT(encounter_id) DO UPDATE SET
                facility=excluded.facility,encounter_date=excluded.encounter_date,
                disposition=excluded.disposition,wait_minutes=excluded.wait_minutes""",records)
            conn.execute("INSERT INTO import_batches(file_hash,row_count) VALUES(?,?)",(digest,len(records)))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    return {"loaded":len(records),"already_processed":False,"sha256":digest}

def metrics(db_path):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory=sqlite3.Row
        return [dict(row) for row in conn.execute("""SELECT facility,COUNT(*) AS encounters,
            ROUND(AVG(wait_minutes),2) AS mean_wait_minutes,
            ROUND(100*AVG(CASE WHEN disposition='admitted' THEN 1.0 ELSE 0 END),2) AS admission_pct,
            SUM(CASE WHEN wait_minutes>60 THEN 1 ELSE 0 END) AS long_wait_count
            FROM encounters GROUP BY facility ORDER BY facility""")]
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--csv",required=True)
    parser.add_argument("--db",required=True)
    parser.add_argument("--report",required=True)
    args=parser.parse_args()
    load=load_file(args.csv,args.db)
    Path(args.report).write_text(json.dumps({"load":load,"facilities":metrics(args.db)},indent=2)+"\n")
    print(f"Loaded {load['loaded']} records (already processed: {load['already_processed']})")
if __name__=="__main__":main()
