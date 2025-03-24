import logging
from typing import AsyncContextManager, List, Optional

from aihub_lib.runners.Runner import Runner

from aihub_bot.runners.lifetime.lifetime_manager import lifetime_manager

logger = logging.getLogger(__name__)


class BotRunner(Runner):
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
