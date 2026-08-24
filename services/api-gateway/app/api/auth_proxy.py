import httpx
from fastapi import APIRouter, Request, Response, status

from app.clients.auth_client import AuthClient, HOP_BY_HOP_HEADERS

router = APIRouter(prefix="/api/v1/auth", tags=["auth-proxy"])


@router.api_route("", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy_auth_request(request: Request, path: str = "") -> Response:
    try:
        upstream_response = await AuthClient().forward(request, path)
    except httpx.RequestError:
        return Response(
            content=b'{"detail":"Auth service unavailable."}',
            media_type="application/json",
            status_code=status.HTTP_502_BAD_GATEWAY,
        )

    headers = {
        key: value
        for key, value in upstream_response.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=headers,
    )
