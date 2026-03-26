"""Logging estruturado em JSON para observabilidade."""

import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any

from src.core.config import app_config


class JsonFormatter(logging.Formatter):
    """Formata logs como JSON para fácil parsing por ferramentas de observabilidade."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": "collector",
            "environment": app_config.environment,
        }

        # Adiciona campos extras se existirem
        if hasattr(record, "group_id"):
            log_entry["group_id"] = record.group_id
        if hasattr(record, "message_id"):
            log_entry["message_id"] = record.message_id
        if hasattr(record, "operation"):
            log_entry["operation"] = record.operation
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms
        if hasattr(record, "count"):
            log_entry["count"] = record.count

        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else "Unknown",
                "message": str(record.exc_info[1]),
            }

        return json.dumps(log_entry, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """Retorna logger configurado com output JSON."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, app_config.log_level.upper(), logging.INFO))
        logger.propagate = False

    return logger
