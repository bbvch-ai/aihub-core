from aihub_lib.infrastructure.logging.logger import enable_logging

from aihub_mcp.runners.MCPRunner import MCPRunner
from aihub_mcp.settings.MCPSettings import MCPSettings

enable_logging()

runner = MCPRunner(MCPSettings())
app = runner.create_app()
