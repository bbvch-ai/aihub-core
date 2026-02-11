#!/bin/bash
# PreToolUse hook: Block access to sensitive files (credentials, secrets, locks).
# Exit code 2 blocks the tool call with a message.

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // .tool_input.command // empty')

# Check against sensitive file patterns
case "$file_path" in
  *.env|*.env.*|*/.env)
    echo "BLOCKED: Access to .env files is not allowed. These contain secrets." >&2
    exit 2
    ;;
  *.pem|*.key)
    echo "BLOCKED: Access to certificate/key files is not allowed." >&2
    exit 2
    ;;
  *credentials*|*secret*)
    echo "BLOCKED: Access to credential/secret files is not allowed." >&2
    exit 2
    ;;
  */certs/*)
    echo "BLOCKED: Access to certificate directories is not allowed." >&2
    exit 2
    ;;
  *_TOKEN*|*_token*)
    echo "BLOCKED: Access to token files is not allowed." >&2
    exit 2
    ;;
  */poetry.lock)
    echo "BLOCKED: Manual edits to poetry.lock are not allowed. Use 'poetry add/remove/update' instead." >&2
    exit 2
    ;;
esac

exit 0
