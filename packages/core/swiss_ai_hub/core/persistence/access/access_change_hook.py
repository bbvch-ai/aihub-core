from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner import OpenWebuiProvisioner

logger = logging.getLogger(__name__)

_DEBOUNCE_SECONDS = 2.0


class AccessChangeHook:
    """Reflects access changes into OpenWebUI groups and grants.

    `RoleEntity`, `TenantMetadataEntity` and `UserTenantRoleEntity` call `notify` after every insert, save and
    delete through a document (Beanie has no global signals), and the sync is debounced.
    """

    _connected: ClassVar[bool] = False
    _debounce_task: ClassVar[asyncio.Task | None] = None
    _provisioner: ClassVar[OpenWebuiProvisioner | None] = None

    @classmethod
    def connect(cls, provisioner: OpenWebuiProvisioner) -> None:
        """Starts syncing OpenWebUI access on access changes; until then `notify` does nothing.

        Rapid mutations are debounced: only the last change in a 2-second quiet window triggers sync.
        """
        if cls._connected:
            return

        cls._provisioner = provisioner
        logger.info("AccessChangeHook connected")
        cls._connected = True

    @classmethod
    def notify(cls) -> None:
        """Schedules an OpenWebUI access sync after an access entity changed."""
        if not cls._connected:
            return
        logger.info("Access entity changed, scheduling OpenWebUI sync")
        cls._schedule_sync()

    @classmethod
    def _schedule_sync(cls) -> None:
        if cls._debounce_task and not cls._debounce_task.done():
            cls._debounce_task.cancel()
        cls._debounce_task = asyncio.create_task(cls._debounced_sync())

    @classmethod
    async def _debounced_sync(cls) -> None:
        await asyncio.sleep(_DEBOUNCE_SECONDS)
        await cls._provisioner.sync_access()
