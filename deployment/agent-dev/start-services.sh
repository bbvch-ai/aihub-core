#!/bin/bash
# Startup script for agent development container
# Starts both code-server (VS Code) and OpenCode Server

set -e

echo "================================================"
echo "Starting Agent Development Environment"
echo "================================================"

# Start OpenCode Server
echo ""
echo "🤖 Starting OpenCode Server on port 8080..."
opencode-server --host 0.0.0.0 --port 8080 &
OPENCODE_PID=$!

# Wait a moment for OpenCode to start
sleep 2

# Start code-server (VS Code)
echo "📝 Starting code-server (VS Code) on port 8443..."
echo "   Password: ${PASSWORD:-developer}"
echo ""

code-server \
  --bind-addr 0.0.0.0:8443 \
  --auth password \
  --disable-telemetry \
  --disable-update-check \
  /workspace/agent &
CODESERVER_PID=$!

# Wait a moment for code-server to start
sleep 3

echo "================================================"
echo "✅ Services Started Successfully!"
echo "================================================"
echo ""
echo "Access Points:"
echo "  VS Code:    http://localhost:${VSCODE_PORT:-8443}"
echo "  OpenCode:   http://localhost:${OPENCODE_PORT:-8080}"
echo "  Phoenix:    http://localhost:6006"
echo ""
echo "Credentials:"
echo "  VS Code Password: ${PASSWORD:-developer}"
echo ""
echo "Agent Files: /workspace/agent"
echo "================================================"

# Keep container running and wait for both processes
wait $OPENCODE_PID $CODESERVER_PID
