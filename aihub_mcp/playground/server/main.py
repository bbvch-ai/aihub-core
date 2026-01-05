#!/usr/bin/env python
import argparse
import sys

from pydantic import SecretStr


def print_examples(host: str, port: int, api_key: str | None) -> None:
    """Print example curl commands for testing."""
    base_url = f"http://{host}:{port}"
    auth_header = f'-H "Authorization: Bearer {api_key}" \\\n     ' if api_key else ""

    print("\n" + "=" * 60)
    print("MCP Server Playground")
    print("=" * 60)
    print(f"\nServer running at: {base_url}/mcp")
    print(f"Authentication: {'Enabled (key: ' + api_key + ')' if api_key else 'Disabled'}")

    print("\n" + "-" * 60)
    print("Example Commands:")
    print("-" * 60)

    print("\n1. List available tools:")
    print(f"""
   curl -X POST {base_url}/mcp \\
     -H "Content-Type: application/json" \\
     {auth_header}-d '{{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}}'
""")

    print("2. List available resources:")
    print(f"""
   curl -X POST {base_url}/mcp \\
     -H "Content-Type: application/json" \\
     {auth_header}-d '{{"jsonrpc": "2.0", "id": 1, "method": "resources/list"}}'
""")

    print("3. Get server capabilities:")
    init_params = (
        '"params": {"protocolVersion": "2024-11-05", '
        '"capabilities": {}, "clientInfo": {"name": "playground", "version": "1.0"}}'
    )
    print(f"""
   curl -X POST {base_url}/mcp \\
     -H "Content-Type: application/json" \\
     {auth_header}-d '{{"jsonrpc": "2.0", "id": 1, "method": "initialize", {init_params}}}'
""")

    print("4. Call a tool (after agents are discovered):")
    tool_params = '"params": {"name": "<tool_name>", "arguments": {"message": "Hello!"}}'
    print(f"""
   curl -X POST {base_url}/mcp \\
     -H "Content-Type: application/json" \\
     {auth_header}-d '{{"jsonrpc": "2.0", "id": 1, "method": "tools/call", {tool_params}}}'
""")

    print("-" * 60)
    print("Press Ctrl+C to stop the server")
    print("-" * 60 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="MCP Server Playground")
    parser.add_argument("--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8001, help="Server port (default: 8001)")
    parser.add_argument("--api-key", default=None, help="API key for authentication (optional in playground)")
    args = parser.parse_args()

    # Import here to avoid loading everything just for --help
    from aihub_mcp.runners.MCPRunner import MCPRunner
    from aihub_mcp.settings.MCPSettings import MCPSettings

    settings = MCPSettings(
        HOST=args.host,
        PORT=args.port,
        API_KEY=SecretStr(args.api_key) if args.api_key else None,
        REQUIRE_AUTH=False,  # Playground doesn't require auth for convenience
        TRACING_ENABLED=False,  # Simpler output for playground
    )

    print_examples(args.host, args.port, args.api_key)

    runner = MCPRunner(settings)
    try:
        runner.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)


if __name__ == "__main__":
    main()
