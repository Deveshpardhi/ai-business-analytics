import json
import logging
import os
import re
from datetime import datetime, timezone


SAFE_EXTRA_FIELDS = (
    "event",
    "error_type",
    "status",
    "provider",
    "analysis_run_id",
    "dataset_version_id",
    "llm_auto_limit",
    "cors_origin_count",
)


def _redact_sensitive_text(value):
    text = str(value)

    sensitive_environment_variables = (
        "GEMINI_API_KEY",
        "AZURE_OPENAI_API_KEY",
    )

    for variable in sensitive_environment_variables:
        secret = os.getenv(variable)

        if secret:
            text = text.replace(
                secret,
                "[REDACTED]",
            )

    # Defensive redaction for Bearer credentials.
    text = re.sub(
        r"Bearer\s+[A-Za-z0-9._~+/=-]+",
        "Bearer [REDACTED]",
        text,
        flags=re.IGNORECASE,
    )

    return text


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": _redact_sensitive_text(
                record.getMessage()
            ),
        }

        for field in SAFE_EXTRA_FIELDS:
            if hasattr(record, field):
                payload[field] = getattr(
                    record,
                    field,
                )

        return json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
        )


def configure_logging(level="INFO"):
    """
    Configure logging for the application namespace.

    Uvicorn's own access/error logging is intentionally
    left untouched.
    """
    app_logger = logging.getLogger("app")

    app_logger.handlers.clear()
    app_logger.setLevel(level)
    app_logger.propagate = False

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    app_logger.addHandler(handler)
