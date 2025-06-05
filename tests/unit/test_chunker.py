import pytest
from ingestion.chunker import chunk_spec, MAX_CHUNK_SIZE


def test_chunk_spec_with_empty_string():
    # An empty string is valid YAML → safe_load returns None → yaml.safe_dump(None) == "null\n"
    chunks = chunk_spec("empty", "")
    assert len(chunks) == 1
    assert chunks[0].path == "empty"
    assert chunks[0].content == "null\n"
    assert chunks[0].chunk_index == 0


def test_chunk_spec_with_empty_dict():
    # A dict → JSON dumped to "{}" → safe_load("{})") → {} → yaml.safe_dump → "{}\n"
    chunks = chunk_spec("d", {})
    assert len(chunks) == 1
    assert chunks[0].path == "d"
    assert chunks[0].content == "{}\n"
    assert chunks[0].chunk_index == 0


def test_chunk_spec_with_invalid_yaml():
    # Invalid YAML → safe_load raises → fallback to original text
    bad = "::: not valid yaml :::"
    chunks = chunk_spec("bad", bad)
    assert len(chunks) == 1
    assert chunks[0].path == "bad"
    assert chunks[0].content == bad
    assert chunks[0].chunk_index == 0


def test_chunk_spec_large_document():
    # Generate a string larger than 2× MAX_CHUNK_SIZE + 100
    text = "x" * (MAX_CHUNK_SIZE * 2 + 100)
    chunks = chunk_spec("big", text)
    # Should split into 3 chunks
    assert len(chunks) == 3
    # Each chunk_index increments by 1
    assert [c.chunk_index for c in chunks] == [0, 1, 2]
    # Reassembling yields the original text
    assert "".join(c.content for c in chunks) == text
