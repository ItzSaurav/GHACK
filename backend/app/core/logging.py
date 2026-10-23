"""Privacy-conscious structured logging that sanitizes sensitive citizen information."""

import logging
import re
import sys

# Regex patterns for sensitive data redaction
REDACTION_PATTERNS = [
    (r"\b\d{4}\s*\d{4}\s*\d{4}\b", "[REDACTED-AADHAAR]"),
    (r"\b\d{10,12}\b", "[REDACTED-NUMERIC-ID]"),
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[REDACTED-EMAIL]"),
    (r"(?i)(password|secret|token|pin)[\s\:\=]+[^\s]+", r"\1=[REDACTED]"),
]


class PrivacySanitizingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        for pattern, replacement in REDACTION_PATTERNS:
            msg = re.sub(pattern, replacement, msg)
        return msg


def setup_privacy_logger(name: str = "scheme_assistant") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        fmt = PrivacySanitizingFormatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")
        handler.setFormatter(fmt)
        logger.addHandler(handler)

    return logger


logger = setup_privacy_logger()
