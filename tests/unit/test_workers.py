# app/tests/unit/test_workers.py

import pytest

# Import the Celery task from the ingestion worker
from app.workers.ingest_worker import run_ingestion_job


def test_run_ingestion_job_has_delay_method():
    """
    Ensure that the `run_ingestion_job` function is decorated as a Celery task,
    i.e., has a `.delay()` attribute.
    """
    assert hasattr(run_ingestion_job, "delay"), "run_ingestion_job should have a 'delay' method"
    assert callable(run_ingestion_job.delay), "'delay' should be callable"
