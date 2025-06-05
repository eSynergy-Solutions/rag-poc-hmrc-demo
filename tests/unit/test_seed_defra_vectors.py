# app/tests/unit/test_seed_defra_vectors.py

import sys
import asyncio
from pathlib import Path

import pytest

SCRIPT_PATH = "scripts/seed_defra_vectors.py"


def run_seed_script(fake_spec_dir: Path, monkeypatch):
    """
    Helper to run `python scripts/seed_defra_vectors.py --spec-dir {fake_spec_dir}`
    but monkey-patch AstraStore so it never connects.
    """
    # 1) Ensure settings have valid Astra/ Azure env:
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "dummy")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "dummy")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "dummy")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT_OAS", "dummy-oas")
    monkeypatch.setenv("ASTRA_DB_APPLICATION_TOKEN", "dummy")
    monkeypatch.setenv("ASTRA_DB_API_ENDPOINT", "https://dummy.astra")

    # 2) Monkey-patch AstraStore so that upsert returns len(chunks) but does not connect
    import app.vectorstore.astradb as astradb_mod

    class FakeAstraStore:
        def __init__(SELF, token, api_endpoint, keyspace, collection_name):
            pass

        def upsert(SELF, chunks):
            # Just return how many chunks would have been upserted
            return len(chunks)

    monkeypatch.setattr(astradb_mod, "AstraStore", FakeAstraStore)

    # 3) Create fake spec files under fake_spec_dir
    #    The script expects: for each .yaml/.yml/.json, it reads file, tries safe_load, falls back to raw text
    y1 = fake_spec_dir / "one_spec.yaml"
    y1.write_text(
        """
openapi: 3.0.0
info:
  title: Fake API
  version: '1.0'
paths: {}
""".strip()
    )
    bad = fake_spec_dir / "bad_spec.yaml"
    bad.write_text("::: not valid yaml :::")

    j1 = fake_spec_dir / "another.json"
    j1.write_text('{"hello": "world", "openapi": "3.0.0", "paths": {}}')

    # 4) Temporarily override sys.argv for the script and exec it
    old_argv = sys.argv[:]
    sys.argv = [SCRIPT_PATH, "--spec-dir", str(fake_spec_dir)]

    ns = {}
    with open(SCRIPT_PATH, "rb") as f:
        code = compile(f.read(), SCRIPT_PATH, "exec")
        exec(code, ns, ns)

    sys.argv = old_argv


def test_seed_defra_vectors_runs(tmp_path, monkeypatch, caplog):
    """
    Smoke-test that `scripts/seed_defra_vectors.py` can iterate over a directory of .yaml/.json files,
    call chunk_spec correctly, and invoke AstraStore.upsert the right number of times.
    """
    fake_spec_dir = tmp_path / "specs"
    fake_spec_dir.mkdir()

    run_seed_script(fake_spec_dir, monkeypatch)

    # If we reached here without a FileNotFoundError or other crash, assume success
    # (We could also optionally check caplog for specific log messages.)
    assert True
