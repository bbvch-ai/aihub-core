#!/bin/bash
# PreToolUse hook: Block access to sensitive files (credentials, secrets, locks).
# Exit code 2 blocks the tool call with a message.

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // .tool_input.command // empty')

# Check against sensitive file patterns
case "$file_path" in
  *.env|*/.env)
    # Block .env (live secrets) but allow .env.dev and .env.prod (checked-in templates)
    echo "BLOCKED: Access to .env is not allowed. It contains secrets. Use .env.dev or .env.prod instead." >&2
    exit 2
    ;;
  *.pem|*.key)
    echo "BLOCKED: Access to certificate/key files is not allowed." >&2
    exit 2
    ;;
  *credentials.json|*credentials.yaml|*credentials.yml|*client_secret*)
    echo "BLOCKED: Access to credential files is not allowed." >&2
    exit 2
    ;;
  */certs/*.pem|*/certs/*.key|*/certs/*.crt)
    echo "BLOCKED: Access to certificate files is not allowed." >&2
    exit 2
    ;;
  */uv.lock)
    echo "BLOCKED: Manual edits to uv.lock are not allowed. Use 'uv add/remove' instead." >&2
    exit 2
    ;;
esac

exit 0
