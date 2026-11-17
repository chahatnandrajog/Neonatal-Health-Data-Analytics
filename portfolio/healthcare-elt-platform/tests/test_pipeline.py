import csv
import pytest
from healthcare_elt.pipeline import validate_file,load_file,metrics

HEAD=["encounter_id","facility","encounter_date","disposition","wait_minutes"]
ROWS=[["e1","Boston","2026-11-01","admitted","45"],["e2","Boston","2026-11-02","discharged","90"],["e3","Raleigh","2026-11-02","transferred","20"]]
@pytest.fixture
def paths(tmp_path):return tmp_path/"data.csv",tmp_path/"data.db"
def write(path,rows,head=HEAD):
    with path.open("w",newline="") as f:
        writer=csv.writer(f)
        writer.writerow(head)
        writer.writerows(rows)
def test_load(paths):
    csvpath,db=paths;write(csvpath,ROWS)
    assert load_file(csvpath,db)["loaded"]==3
def test_idempotent(paths):
    csvpath,db=paths;write(csvpath,ROWS);load_file(csvpath,db)
    assert load_file(csvpath,db)["already_processed"]
def test_mean_wait(paths):
    csvpath,db=paths;write(csvpath,ROWS);load_file(csvpath,db)
    assert metrics(db)[0]["mean_wait_minutes"]==67.5
def test_admission_rate(paths):
    csvpath,db=paths;write(csvpath,ROWS);load_file(csvpath,db)
    assert metrics(db)[0]["admission_pct"]==50
def test_duplicate(paths):
    csvpath,_=paths;write(csvpath,ROWS+[ROWS[0]])
    with pytest.raises(ValueError,match="duplicate"):validate_file(csvpath)
def test_missing_header(paths):
    csvpath,_=paths;write(csvpath,[],HEAD[:-1])
    with pytest.raises(ValueError,match="columns"):validate_file(csvpath)
def test_bad_date(paths):
    csvpath,_=paths;write(csvpath,[["e1","Boston","2026-02-30","admitted","45"]])
    with pytest.raises(ValueError,match="date"):validate_file(csvpath)
def test_bad_status(paths):
    csvpath,_=paths;write(csvpath,[["e1","Boston","2026-11-01","unknown","45"]])
    with pytest.raises(ValueError,match="disposition"):validate_file(csvpath)
def test_negative_wait(paths):
    csvpath,_=paths;write(csvpath,[["e1","Boston","2026-11-01","admitted","-1"]])
    with pytest.raises(ValueError,match="range"):validate_file(csvpath)
def test_bad_input_preserves_data(paths):
    csvpath,db=paths;write(csvpath,ROWS);load_file(csvpath,db)
    write(csvpath,[["e4","Boston","2026-11-01","admitted","-10"]])
    with pytest.raises(ValueError):load_file(csvpath,db)
    assert sum(x["encounters"] for x in metrics(db))==3
def test_upsert(paths):
    csvpath,db=paths;write(csvpath,ROWS);load_file(csvpath,db)
    write(csvpath,[["e1","Boston","2026-11-01","admitted","120"]]);load_file(csvpath,db)
    assert metrics(db)[0]["mean_wait_minutes"]==105
