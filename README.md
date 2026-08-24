# EventFlow

EventFlow is a phased event/workflow platform. Phase 1 establishes the backend foundation: an API Gateway, an Auth Service, PostgreSQL for auth data, Redis for later session/rate-limit work, request IDs, migrations, JWT access tokens, and refresh-token rotation.

## Run Phase 1 Locally

From the repo root:

```bash
docker compose up --build
```

The auth-service runs Alembic automatically on container start:

```bash
alembic upgrade head
```

If you need to run migrations manually:

```bash
docker compose run --rm auth-service alembic upgrade head
```

Health checks:

```bash
curl http://localhost:8000/health
curl http://localhost:8001/ready
```

Run the full auth flow through the gateway:

```bash
bash scripts/phase1-auth-flow.sh
```

Or test manually:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secure-password","name":"Test User"}'
```

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secure-password"}'
```

Use the returned `access_token`:

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## What's Next

Phase 2: Workflow CRUD.
