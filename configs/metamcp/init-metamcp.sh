#!/bin/sh
# MetaMCP init script — creates admin user, namespace, and endpoint.
# Runs as an init container after MetaMCP is healthy.
# Idempotent: safe to run multiple times.
set -e

BACKEND_URL="http://metamcp:12009"

echo "=== MetaMCP Init ==="

# Install curl (not included in postgres base image)
apt-get update -qq && apt-get install -y -qq --no-install-recommends curl > /dev/null 2>&1
echo "  -> curl installed"

# --- 1. Create admin user via Better Auth sign-up API ---
echo "Creating admin user (${METAMCP_ADMIN_EMAIL})..."
SIGNUP_RESPONSE=$(curl -sf -X POST "${BACKEND_URL}/api/auth/sign-up/email" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${METAMCP_ADMIN_EMAIL}\",\"password\":\"${METAMCP_ADMIN_PASSWORD}\",\"name\":\"${METAMCP_ADMIN_NAME}\"}") || SIGNUP_RESPONSE="SIGNUP_FAILED"

if echo "$SIGNUP_RESPONSE" | grep -q "token"; then
  echo "  -> User created successfully."
elif echo "$SIGNUP_RESPONSE" | grep -q "USER_ALREADY_EXISTS"; then
  echo "  -> User already exists, skipping."
else
  echo "  -> Sign-up returned: $SIGNUP_RESPONSE (will retry with sign-in check)"
  # Check if user exists via DB as a fallback
  USER_COUNT=$(psql -qtA -c "SELECT COUNT(*) FROM users WHERE email = '${METAMCP_ADMIN_EMAIL}';")
  if [ "$USER_COUNT" -gt 0 ]; then
    echo "  -> User exists in database, continuing."
  else
    echo "  -> WARNING: Could not create admin user."
  fi
fi

# --- 2. Create public namespace via direct SQL ---
echo "Creating 'default' namespace..."
NAMESPACE_EXISTS=$(psql -qtA -c "SELECT COUNT(*) FROM namespaces WHERE name = 'default' AND user_id IS NULL;")
if [ "$NAMESPACE_EXISTS" -gt 0 ]; then
  echo "  -> Public namespace 'default' already exists, skipping."
else
  psql -q -c "INSERT INTO namespaces (uuid, name, description, user_id, created_at, updated_at) VALUES (gen_random_uuid(), 'default', 'Default namespace for AI Hub agents', NULL, NOW(), NOW());"
  echo "  -> Created namespace."
fi
NAMESPACE_UUID=$(psql -qtA -c "SELECT uuid FROM namespaces WHERE name = 'default' AND user_id IS NULL LIMIT 1;")

# --- 3. Create public endpoint (auth disabled) via direct SQL ---
echo "Creating 'default' endpoint..."
ENDPOINT_EXISTS=$(psql -qtA -c "SELECT COUNT(*) FROM endpoints WHERE name = 'default' AND user_id IS NULL;")
if [ "$ENDPOINT_EXISTS" -gt 0 ]; then
  echo "  -> Public endpoint 'default' already exists, skipping."
else
  psql -q -c "INSERT INTO endpoints (uuid, name, description, namespace_uuid, enable_api_key_auth, use_query_param_auth, enable_oauth, user_id, created_at, updated_at) VALUES (gen_random_uuid(), 'default', 'Default endpoint for AI Hub agents', '${NAMESPACE_UUID}', false, false, false, NULL, NOW(), NOW());"
  echo "  -> Created endpoint."
fi

echo "=== MetaMCP Init Complete ==="
echo "  Admin user:  ${METAMCP_ADMIN_EMAIL}"
echo "  Namespace:   default (${NAMESPACE_UUID})"
echo "  Endpoint:    http://metamcp:12008/metamcp/default/mcp (auth: disabled)"