"""Main entry point for the MCP server."""

import logging

from aihub_mcp.runners.MCPRunner import MCPRunner
from aihub_mcp.settings.MCPSettings import MCPSettings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main() -> None:
    """Start the MCP server."""
    logger.info("Initializing Swiss AI Hub MCP Server...")

    settings = MCPSettings()

    if settings.DEBUG:
        logging.getLogger().setLevel(logging.DEBUG)

    runner = MCPRunner(settings)
    runner.run()


if __name__ == "__main__":
    main()
