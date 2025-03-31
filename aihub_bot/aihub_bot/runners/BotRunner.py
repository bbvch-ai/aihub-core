import logging
from typing import AsyncContextManager, List, Optional

from aihub_lib.runners.Runner import Runner

from aihub_bot.runners.lifetime.lifetime_manager import lifetime_manager

logger = logging.getLogger(__name__)


class BotRunner(Runner):
    """
    A concrete implementation of Runner specialized for bot frameworks and conversational services.

    ### Why Use BotRunner?
    `BotRunner` extends the base `Runner` class with features specific to bot services:
    - Uses a dedicated bot lifetime manager for handling bot-specific startup/shutdown
    - Provides appropriate defaults for bot service titles and descriptions
    - Maintains the same consistent API as other runners

    ### Key Features
    - **Bot Lifecycle Management:** Uses a bot-specific lifetime manager that handles bot connections
      and resources.
    - **Consistent Interface:** Follows the same patterns as other runners for mounting controllers
      and configuring the application.
    - **Specialized Defaults:** Pre-configured with appropriate titles and settings for bot services.

    ### Usage
    ```python
    runner = BotRunner(api_path="/api/v1", title="My Bot Service", debug=True)
    runner.mount(BotController())  # Mount bot controllers
    app = runner.get_app()  # Get the FastAPI instance
    ```

    Run the resulting `app` using `uvicorn` or another ASGI server.
    """

    def __init__(
        self,
        api_path: str = "/api/v1",
        title: str = "AI Hub Bot Service",
        description: str = "AI Hub Bots",
        origins: Optional[List[str]] = None,
        debug: bool = False,
    ):
        super().__init__(api_path, title, description, origins, debug)

    @property
    def lifetime_manager(self) -> AsyncContextManager:
        return lifetime_manager
