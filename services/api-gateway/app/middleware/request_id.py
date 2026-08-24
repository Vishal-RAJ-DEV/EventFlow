import logging
from time import perf_counter
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import request_id_context

logger = logging.getLogger("api_gateway.requests")


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-Id") or str(uuid4())
        request.state.request_id = request_id

        token = request_id_context.set(request_id)
        start_time = perf_counter()

        try:
            response = await call_next(request)
        finally:
            duration_ms = round((perf_counter() - start_time) * 1000, 2)
            logger.info(
                "request completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                },
            )
            request_id_context.reset(token)

        response.headers["X-Request-Id"] = request_id
        return response
