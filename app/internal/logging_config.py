"""Logging setup for the API.

Call setup_logging() once, before anything else emits a record. It reconfigures
the uvicorn loggers too, so everything -- ours, uvicorn's and any library's --
lands in the same place with the same shape.

Records made while serving a request carry that request's id and the account
that made it, so a single upload can be followed across modules. Both come from
context variables the request middleware sets; lines logged outside a request
(startup, shutdown, scheduled jobs) carry no context and show none.

Configured by environment:
    LOG_LEVEL   DEBUG | INFO | WARNING | ERROR      (default INFO)
    LOG_FORMAT  plain | json                        (default plain)
    LOG_FILE    path to also write to, rotating     (default none)
    LOG_SQL     1 to include SQLAlchemy statements  (default off)
"""
from __future__ import annotations

import json
import logging
import logging.config
import os
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
user_var: ContextVar[str] = ContextVar("user", default="-")

# Attributes LogRecord always has; anything else an extra= added is ours and
# belongs in the JSON output.
_STANDARD = frozenset(logging.LogRecord("", 0, "", 0, "", None, None).__dict__) | {
    "asctime", "message", "taskName", "request_id", "user",
}


class ContextFilter(logging.Filter):
    """Stamps every record with the request it belongs to."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        record.user = user_var.get()
        return True


class JsonFormatter(logging.Formatter):
    """One JSON object per line, for when the logs are shipped somewhere."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
            "user": getattr(record, "user", "-"),
        }
        for key, value in record.__dict__.items():
            if key not in _STANDARD and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


class PlainFormatter(logging.Formatter):
    """Readable output that only shows a request context when there is one.

    Startup, shutdown and scheduled jobs run outside any request, so printing
    empty placeholders on those lines would be noise on a large share of them.
    """

    def __init__(self):
        super().__init__("%(asctime)s %(levelname)-8s %(name)s:%(context)s %(message)s",
                         datefmt="%Y-%m-%d %H:%M:%S")

    def format(self, record: logging.LogRecord) -> str:
        request_id = getattr(record, "request_id", "-")
        user = getattr(record, "user", "-")

        if request_id == "-":
            record.context = ""
        elif user == "-":
            record.context = f" [{request_id}]"
        else:
            record.context = f" [{request_id} {user}]"

        return super().format(record)


def setup_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    fmt = "json" if os.getenv("LOG_FORMAT", "plain").lower() == "json" else "plain"
    log_file = os.getenv("LOG_FILE")
    sql = os.getenv("LOG_SQL", "").lower() in ("1", "true", "yes")

    handlers: dict[str, dict] = {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": fmt,
            "filters": ["context"],
        }
    }

    if log_file:
        os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": log_file,
            "maxBytes": 16 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8",
            "formatter": fmt,
            "filters": ["context"],
        }

    logging.config.dictConfig({
        "version": 1,
        # uvicorn configures its loggers before importing the app, so leave them
        # attached and take them over below rather than switching them off.
        "disable_existing_loggers": False,
        "filters": {"context": {"()": ContextFilter}},
        "formatters": {
            "plain": {"()": PlainFormatter},
            "json": {"()": JsonFormatter},
        },
        "handlers": handlers,
        "root": {"level": level, "handlers": list(handlers)},
        "loggers": {
            "app": {"level": level, "handlers": list(handlers), "propagate": False},
            "uvicorn": {"level": "INFO", "handlers": list(handlers), "propagate": False},
            "uvicorn.error": {"level": "INFO", "handlers": list(handlers), "propagate": False},
            # Our own middleware logs requests with timing and identity, so
            # uvicorn's one-line version would only duplicate it.
            "uvicorn.access": {"level": "CRITICAL", "handlers": [], "propagate": False},
            "sqlalchemy.engine": {
                "level": "INFO" if sql else "WARNING",
                "handlers": list(handlers),
                "propagate": False,
            },
            "apscheduler": {"level": "WARNING", "handlers": list(handlers), "propagate": False},
        },
    })

    logging.getLogger("app.startup").info(
        "Logging ready", extra={"log_level": level, "format": fmt, "file": log_file or "none"}
    )
