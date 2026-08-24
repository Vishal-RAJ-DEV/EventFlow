from urllib.parse import urljoin

import httpx
from starlette.requests import Request

from app.core.config import AUTH_SERVICE_URL

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


class AuthClient:
    def __init__(self, base_url: str = AUTH_SERVICE_URL) -> None:
        self.base_url = base_url.rstrip("/")

    async def forward(self, request: Request, path: str) -> httpx.Response:
        headers = self._build_forward_headers(request)
        body = await request.body()
        target_url = self._build_target_url(path, request.url.query)

        async with httpx.AsyncClient() as client:
            return await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
            )

    def _build_forward_headers(self, request: Request) -> dict[str, str]:
        headers = {
            key: value
            for key, value in request.headers.items()
            if key.lower() not in HOP_BY_HOP_HEADERS and key.lower() != "host"
        }
        headers["X-Request-Id"] = request.state.request_id
        return headers

    def _build_target_url(self, path: str, query: str) -> str:
        auth_path = f"/auth/{path}".rstrip("/")
        target_url = urljoin(f"{self.base_url}/", auth_path.lstrip("/"))

        if query:
            target_url = f"{target_url}?{query}"

        return target_url
