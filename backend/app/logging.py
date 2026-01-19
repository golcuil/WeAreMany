import json
import logging
import time
from typing import Any, Dict

SENSITIVE_HEADERS = {"authorization", "cookie"}


def redact_headers(headers: Dict[str, Any]) -> Dict[str, Any]:
    redacted = {}
    for key, value in headers.items():
        if key.lower() in SENSITIVE_HEADERS:
            redacted[key] = "[redacted]"
        else:
            redacted[key] = value
    return redacted


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "message": record.getMessage(),
            "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
        }
        if isinstance(record.args, dict):
            payload.update(record.args)
        return json.dumps(payload)


def configure_logging() -> logging.Logger:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = [handler]
    return logging.getLogger("backend")
