from fastapi import FastAPI

app = FastAPI(title="EventFlow API Gateway")


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "api-gateway"}
