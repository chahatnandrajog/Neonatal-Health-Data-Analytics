import csv
import json
import tempfile
import unittest
from pathlib import Path
from neonatal_pipeline.core import aggregate, export_json, ingest, read_cohorts

COLUMNS = ["year","group_name","births","low_birth_weight_births","preterm_births","birth_weight_grams_sum"]
ROWS = [[2023,"A",10,2,1,30000],[2023,"B",90,9,18,315000],[2024,"A",20,1,3,64000]]

class AnalyticsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.csv = Path(self.tmp.name)/"input.csv"
        self.db = Path(self.tmp.name)/"cohorts.db"
        self.report = Path(self.tmp.name)/"report.json"
        self.write(ROWS)

    def write(self, rows, cols=COLUMNS):
        with self.csv.open("w",newline="",encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(cols)
            writer.writerows(rows)

    def test_weighted_rates(self):
        self.assertEqual(ingest(self.csv,self.db),3)
        row = aggregate(self.db,"year")[0]
        self.assertEqual(row["births"],100)
        self.assertEqual(row["low_birth_weight_rate_pct"],11)
        self.assertEqual(row["preterm_rate_pct"],19)
        self.assertEqual(row["mean_birth_weight_grams"],3450)

    def test_group_aggregation(self):
        ingest(self.csv,self.db)
        self.assertEqual(aggregate(self.db,"group")[0]["births"],30)

    def test_overall_aggregation(self):
        ingest(self.csv,self.db)
        self.assertEqual(aggregate(self.db,"overall")[0]["births"],120)

    def test_duplicate(self):
        self.write(ROWS+[ROWS[0]])
        with self.assertRaisesRegex(ValueError,"duplicate"):
            read_cohorts(self.csv)

    def test_impossible_counts(self):
        self.write([[2023,"A",10,11,0,30000]])
        with self.assertRaisesRegex(ValueError,"impossible"):
            read_cohorts(self.csv)

    def test_missing_columns(self):
        self.write([],cols=COLUMNS[:-1])
        with self.assertRaisesRegex(ValueError,"columns"):
            read_cohorts(self.csv)

    def test_noninteger(self):
        self.write([[2023,"A","ten",2,1,30000]])
        with self.assertRaisesRegex(ValueError,"integer"):
            read_cohorts(self.csv)

    def test_bad_upload_does_not_replace_data(self):
        ingest(self.csv,self.db)
        self.write([[2024,"A",1,4,0,3000]])
        with self.assertRaises(ValueError):
            ingest(self.csv,self.db)
        self.assertEqual(aggregate(self.db,"overall")[0]["births"],120)

    def test_json_export(self):
        ingest(self.csv,self.db)
        export_json(self.db,self.report)
        payload=json.loads(self.report.read_text())
        self.assertEqual(set(payload),{"annual","overall","by_group"})

    def test_unknown_grouping(self):
        with self.assertRaises(ValueError):
            aggregate(self.db,"year;DROP TABLE cohorts")
