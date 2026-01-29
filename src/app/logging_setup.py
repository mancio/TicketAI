"""Structured logging setup with correlation IDs and redaction."""

import logging
import uuid
from pythonjsonlogger import jsonlogger


class SafeJSONFormatter(jsonlogger.JsonFormatter):
    """JSON formatter that avoids logging raw ticket text."""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        if "ticket_text" in log_record:
            log_record["ticket_text"] = "[REDACTED]"


def create_request_id() -> str:
    return str(uuid.uuid4())[:8]


def setup_logging(log_level: str) -> logging.Logger:
    logger = logging.getLogger("ticketai")
    logger.setLevel(log_level.upper())
    handler = logging.StreamHandler()
    formatter = SafeJSONFormatter()
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)
    return logger
