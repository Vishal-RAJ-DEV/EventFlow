from fastapi import FastAPI

from app.api.auth import router as auth_router

app = FastAPI(title="EventFlow Auth Service")

app.include_router(auth_router)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "auth-service"}
