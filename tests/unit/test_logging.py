# app/tests/unit/test_logging.py

import json
import structlog
from core.logging import logger


def test_logger_emits_json(capsys):
    # Emit a log event
    logger.info("test_event", foo="bar")
    # Capture stdout
    captured = capsys.readouterr()
    output = captured.out.strip()
    # It should be valid JSON
    data = json.loads(output)
    assert data["event"] == "test_event"
    assert data["foo"] == "bar"
    assert "level" in data
    assert "timestamp" in data
