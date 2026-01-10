#!/bin/bash

# ----------------------------
# TheButtonApp Test Script
# ----------------------------

# 1️⃣ Activate the virtual environment
source /Users/stevitaylor/Desktop/TheButtonApp/.venv/bin/activate

# 2️⃣ Start Uvicorn server in the background
echo "Starting FastAPI server..."
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload --log-level debug &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"

# 3️⃣ Wait a few seconds for the server to start
sleep 5

# 4️⃣ Create a test user
echo "Creating test user..."
curl -s -X POST "http://127.0.0.1:8003/users/" \
-H "Content-Type: application/json" \
-d '{
  "email": "testuser@example.com",
  "password": "TestPassword123"
}'
echo -e "\n"

# 5️⃣ Log in to get the access token
echo "Logging in..."
RESPONSE=$(curl -s -X POST "http://127.0.0.1:8003/auth/login" \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "username=testuser@example.com&password=TestPassword123")

# Extract token from JSON
TOKEN=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo "Access token: $TOKEN"
echo -e "\n"

# 6️⃣ Access protected endpoint
echo "Fetching current user info..."
curl -s -X GET "http://127.0.0.1:8003/users/me" \
-H "Authorization: Bearer $TOKEN"
echo -e "\n"

# 7️⃣ Optional: Stop the server (uncomment if you want automatic cleanup)
# kill $SERVER_PID
# echo "Server stopped."
