# app/tests/unit/test_chunker_dict.py

import yaml
from ingestion.chunker import chunk_spec


def test_chunk_spec_with_dict():
    """
    When passed a dict, chunk_spec should JSON-dump then YAML-dump it.
    For a tiny dict, that yields a single chunk whose content starts with the YAML representation.
    """
    spec = {"hello": "world"}
    chunks = chunk_spec("my_path", spec)
    assert len(chunks) == 1
    c = chunks[0]
    assert c.path == "my_path"
    # YAML of {"hello": "world"} is "hello: world\n"
    assert c.content.startswith("hello: world")
    assert c.chunk_index == 0
