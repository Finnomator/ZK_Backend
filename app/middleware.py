"""Request logging.

Written as raw ASGI rather than BaseHTTPMiddleware because that one buffers the
whole response body to re-emit it, and this API serves firmware images of half a
megabyte a chunk.
"""
from __future__ import annotations

import base64
import logging
import time
import uuid

from app.internal.logging_config import request_id_var, user_var

log = logging.getLogger("app.request")

# Health checks would otherwise be most of the log.
QUIET_PATHS = frozenset({"/ping", "/health", "/metrics"})

SLOW_REQUEST_MS = 3000


def _basic_auth_user(headers: list[tuple[bytes, bytes]]) -> str:
    """Username from HTTP Basic credentials -- the IMEI for a device.

    Taken from the header rather than from the auth dependency so that failed
    logins, which never reach a dependency, are attributed too. The password is
    never touched.
    """
    for key, value in headers:
        if key.lower() != b"authorization":
            continue
        try:
            scheme, _, encoded = value.decode("latin-1").partition(" ")
            if scheme.lower() != "basic":
                return "-"
            return base64.b64decode(encoded).decode("utf-8", "replace").split(":", 1)[0] or "-"
        except Exception:
            return "?"
    return "-"


class RequestLogMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = uuid.uuid4().hex[:8]
        user = _basic_auth_user(scope.get("headers", []))

        id_token = request_id_var.set(request_id)
        user_token = user_var.set(user)

        status = 500
        sent = 0

        async def send_wrapper(message):
            nonlocal status, sent
            if message["type"] == "http.response.start":
                status = message["status"]
            elif message["type"] == "http.response.body":
                sent += len(message.get("body", b""))
            await send(message)

        started = time.perf_counter()
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            # Starlette still turns this into a 500; we just want the traceback
            # attributed to the request that caused it.
            log.exception(
                "Unhandled exception in %s %s", scope.get("method"), scope.get("path"),
                extra={"method": scope.get("method"), "path": scope.get("path")},
            )
            raise
        finally:
            took_ms = (time.perf_counter() - started) * 1000
            path = scope.get("path", "")

            if status >= 500:
                level = logging.ERROR
            elif status >= 400:
                level = logging.WARNING
            elif took_ms >= SLOW_REQUEST_MS:
                level = logging.WARNING
            elif path in QUIET_PATHS:
                level = logging.DEBUG
            else:
                level = logging.INFO

            log.log(
                level,
                "%s %s -> %s in %.0f ms (%d B)",
                scope.get("method"), path, status, took_ms, sent,
                extra={
                    "method": scope.get("method"),
                    "path": path,
                    "query": scope.get("query_string", b"").decode("latin-1") or None,
                    "status": status,
                    "duration_ms": round(took_ms, 1),
                    "response_bytes": sent,
                    "client": (scope.get("client") or ("-", 0))[0],
                },
            )

            request_id_var.reset(id_token)
            user_var.reset(user_token)
