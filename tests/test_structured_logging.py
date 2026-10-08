import json
import logging

from app.core.logging import JsonFormatter


def make_record(message):
    return logging.LogRecord(
        name="app.test",
        level=logging.WARNING,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=(),
        exc_info=None,
    )


def test_json_formatter_produces_structured_log():
    record = make_record(
        "Provider unavailable"
    )

    record.event = (
        "llm_explanation_unavailable"
    )
    record.error_type = "ServerError"
    record.status = 503

    output = JsonFormatter().format(record)
    data = json.loads(output)

    assert data["level"] == "WARNING"
    assert data["logger"] == "app.test"
    assert (
        data["event"]
        == "llm_explanation_unavailable"
    )
    assert data["error_type"] == "ServerError"
    assert data["status"] == 503


def test_api_key_is_redacted(
    monkeypatch,
):
    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "secret-test-key",
    )

    record = make_record(
        "Failure secret-test-key"
    )

    output = JsonFormatter().format(record)

    assert "secret-test-key" not in output
    assert "[REDACTED]" in output
