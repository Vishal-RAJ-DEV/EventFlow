#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000/api/v1/auth}"
EMAIL="phase1-$(date +%s)@example.com"
PASSWORD="secure-password"
NAME="Phase One User"

json_get() {
  python -c "import json,sys; print(json.load(sys.stdin)['$1'])"
}

echo "Registering user through gateway..."
REGISTER_RESPONSE="$(
  curl -sS -X POST "$BASE_URL/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\",\"name\":\"$NAME\"}"
)"
echo "$REGISTER_RESPONSE"

echo
echo "Logging in through gateway..."
LOGIN_RESPONSE="$(
  curl -sS -X POST "$BASE_URL/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}"
)"
echo "$LOGIN_RESPONSE"

ACCESS_TOKEN="$(printf '%s' "$LOGIN_RESPONSE" | json_get access_token)"
REFRESH_TOKEN="$(printf '%s' "$LOGIN_RESPONSE" | json_get refresh_token)"

echo
echo "Refreshing token through gateway..."
REFRESH_RESPONSE="$(
  curl -sS -X POST "$BASE_URL/refresh" \
    -H "Content-Type: application/json" \
    -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}"
)"
echo "$REFRESH_RESPONSE"

ACCESS_TOKEN="$(printf '%s' "$REFRESH_RESPONSE" | json_get access_token)"
REFRESH_TOKEN="$(printf '%s' "$REFRESH_RESPONSE" | json_get refresh_token)"

echo
echo "Fetching current user through gateway..."
ME_RESPONSE="$(
  curl -sS "$BASE_URL/me" \
    -H "Authorization: Bearer $ACCESS_TOKEN"
)"
echo "$ME_RESPONSE"

echo
echo "Logging out through gateway..."
curl -sS -i -X POST "$BASE_URL/logout" \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}"

echo
echo "Done."
