"""Optional Apache Airflow DAG; requires configured Airflow environment."""
from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG("healthcare_encounter_metrics", start_date=datetime(2026,11,1), schedule="0 6 * * *", catchup=False, tags=["portfolio"]) as dag:
    run_elt = BashOperator(
        task_id="validated_pipeline",
        bash_command='cd "$HEALTHCARE_ELT_HOME" && python -m healthcare_elt.pipeline --csv "$HEALTHCARE_ELT_INPUT" --db "$HEALTHCARE_ELT_DB" --report "$HEALTHCARE_ELT_REPORT"',
    )
