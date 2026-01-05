import logging

from aihub_lib.infrastructure.logging.logger import enable_logging

from aihub_mcp.runners.MCPRunner import MCPRunner
from aihub_mcp.settings.MCPSettings import MCPSettings

enable_logging()

logger = logging.getLogger(__name__)


def main() -> None:
    """Start the MCP server."""
    logger.info("Initializing Swiss AI Hub MCP Server...")

    settings = MCPSettings()
    runner = MCPRunner(settings)
    runner.run()


if __name__ == "__main__":
    main()
