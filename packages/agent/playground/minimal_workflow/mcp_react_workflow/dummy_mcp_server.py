"""Minimal MCP server for testing the MCP React agent. Run this before trigger.py.

The ``whoami`` and ``create_ticket`` tools read the bearer token off the incoming request, so a
demo can prove the MCP user-token passthrough end to end: a token sent to the AI Hub API as an
``X-AIHub-User-Token`` header should arrive here as the MCP call's bearer. Connections using a
static API key surface as ``anonymous`` or as the static key — the contrast is the demo.
"""

import base64
import json

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers

mcp = FastMCP("test-tools")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


@mcp.tool()
def whoami() -> str:
    """Report which user the MCP server sees the caller authenticated as."""
    identity = _caller_identity()
    print(f"[whoami] caller identity: {identity}")
    return f"The tool server sees you as: {identity}"


@mcp.tool()
def create_ticket(title: str) -> str:
    """Create a demo support ticket, attributed to the authenticated caller.

    Mirrors the real motivation for user-token passthrough: an external action must record the
    actual user as the actor, not a shared service account.
    """
    identity = _caller_identity()
    print(f"[create_ticket] '{title}' reporter: {identity}")
    return f"Ticket DEMO-1042 '{title}' created. Reporter: {identity}"


def _caller_identity() -> str:
    """Pull a human-readable identity out of the incoming request's bearer token.

    The passthrough forwards the requesting user's token as the bearer. Real deployments send a
    Keycloak JWT; demos may send any opaque string — both are handled.
    """
    # get_http_headers() drops `authorization` by default — it must be explicitly opted in.
    headers = get_http_headers(include={"authorization"})
    authorization = headers.get("authorization", "")
    if not authorization.lower().startswith("bearer "):
        return "anonymous (no bearer token reached the MCP server)"
    token = authorization[len("bearer ") :].strip()
    return _jwt_username(token) or token


def _jwt_username(token: str) -> str | None:
    """Best-effort, UNVERIFIED decode of a JWT payload — demo display only, never trust this."""
    parts = token.split(".")
    if len(parts) != 3:
        return None
    padded_payload = parts[1] + "=" * (-len(parts[1]) % 4)
    try:
        claims = json.loads(base64.urlsafe_b64decode(padded_payload))
    except ValueError:
        return None
    return claims.get("preferred_username") or claims.get("email") or claims.get("sub")


@mcp.resource("config://system")
def system_config() -> str:
    """System configuration and version info."""
    return "System version: 1.0, Environment: test, Max retries: 3"


@mcp.resource("users://{user_id}/profile")
def user_profile(user_id: str) -> str:
    """Look up a user profile by ID."""
    return f"Profile for user {user_id}: name=Test User, role=admin, active=true"


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=9090)
