from fastapi import FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.auth import router as auth_router
from app.core.database import get_engine

app = FastAPI(title="EventFlow Auth Service")

app.include_router(auth_router)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "auth-service"}


@app.get("/ready")
def readiness_check():
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not reachable.",
        ) from exc

    return {"status": "ready", "service": "auth-service"}
