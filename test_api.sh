#!/bin/bash

source /Users/stevitaylor/Desktop/TheButtonApp/.venv/bin/activate

echo "Starting FastAPI server..."
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload &
SERVER_PID=$!

sleep 5

echo "Creating test user..."
curl -s -X POST "http://127.0.0.1:8003/users" \
-H "Content-Type: application/json" \
-d '{
  "email": "testuser@example.com",
  "password": "TestPassword123"
}'
echo ""

echo "Logging in..."
RESPONSE=$(curl -s -X POST "http://127.0.0.1:8003/auth/login" \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "username=testuser@example.com&password=TestPassword123")

TOKEN=$(echo "$RESPONSE" | python3 - <<EOF
import json,sys
try:
    print(json.loads(sys.stdin.read()).get("access_token",""))
except:
    print("")
EOF
)

echo "Access token: $TOKEN"
echo ""

if [ -n "$TOKEN" ]; then
  echo "Fetching current user..."
  curl -s -X GET "http://127.0.0.1:8003/users/me" \
  -H "Authorization: Bearer $TOKEN"
  echo ""
else
  echo "Login failed — no token"
fi

kill $SERVER_PID

