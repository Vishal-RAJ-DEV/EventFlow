from fastapi import FastAPI

from app.api.auth_proxy import router as auth_proxy_router
from app.core.logging import configure_logging
from app.middleware.request_id import RequestIdMiddleware

configure_logging()

app = FastAPI(title="EventFlow API Gateway")

app.add_middleware(RequestIdMiddleware)
app.include_router(auth_proxy_router)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "api-gateway"}
