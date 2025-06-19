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
    - Centralizes TTL configuration for conversation persistence

    ### Key Features
    - **Bot Lifecycle Management:** Uses a bot-specific lifetime manager that handles bot connections
      and resources.
    - **Consistent Interface:** Follows the same patterns as other runners for mounting controllers
      and configuring the application.
    - **Specialized Defaults:** Pre-configured with appropriate titles and settings for bot services.
    - **Centralized TTL Management:** Sets TTL configuration for all controllers in one place.

    ### Usage
    ```python
    runner = BotRunner(api_path="/token/v1", title="My Bot Service", debug=True, conversation_ttl_days=30)
    runner.mount(BotController())  # Mount bot controllers
    app = runner.get_app()  # Get the FastAPI instance
    ```

    Run the resulting `app` using `uvicorn` or another ASGI server.
    """

    def __init__(
        self,
        api_path: str = "/token/v1",
        title: str = "AI Hub Bot Service",
        description: str = "AI Hub Bots",
        origins: Optional[List[str]] = None,
        debug: bool = False,
        conversation_ttl_days: float = 30,
    ):
        super().__init__(api_path, title, description, origins, debug)

        # Store TTL days in app state for lifetime manager to access
        self._base_app.state.conversation_ttl_days = conversation_ttl_days

    @property
    def lifetime_manager(self) -> AsyncContextManager:
        return lifetime_manager
