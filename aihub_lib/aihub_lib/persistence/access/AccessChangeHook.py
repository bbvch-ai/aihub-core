import asyncio
import logging
from typing import Any, ClassVar

from mongoengine import signals

from aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner import OpenWebuiProvisioner
from aihub_lib.persistence.access.entities.RoleEntity import RoleEntity
from aihub_lib.persistence.access.entities.TenantEntity import TenantEntity
from aihub_lib.persistence.access.entities.UserTenantRoleEntity import UserTenantRoleEntity

logger = logging.getLogger(__name__)

_DEBOUNCE_SECONDS = 2.0


class AccessChangeHook:
    _connected: ClassVar[bool] = False
    _debounce_task: ClassVar[asyncio.Task | None] = None

    @classmethod
    def connect(cls) -> None:
        """Wires MongoEngine signals to sync OpenWebUI access on any access entity save/delete.

        Rapid mutations are debounced: only the last change in a 2-second quiet window triggers sync.
        """
        if cls._connected:
            return

        def _on_change(sender: type, document: Any, **kwargs: Any) -> None:
            logger.info("Access entity changed (%s), scheduling OpenWebUI sync", sender.__name__)
            cls._schedule_sync()

        for entity_cls in [RoleEntity, TenantEntity, UserTenantRoleEntity]:
            signals.post_save.connect(_on_change, sender=entity_cls)
            signals.post_delete.connect(_on_change, sender=entity_cls)

        logger.info(
            "AccessChangeHook connected for %s",
            [cls.__name__ for cls in [RoleEntity, TenantEntity, UserTenantRoleEntity]],
        )
        cls._connected = True

    @classmethod
    def _schedule_sync(cls) -> None:
        if cls._debounce_task and not cls._debounce_task.done():
            cls._debounce_task.cancel()
        cls._debounce_task = asyncio.create_task(cls._debounced_sync())

    @classmethod
    async def _debounced_sync(cls) -> None:
        await asyncio.sleep(_DEBOUNCE_SECONDS)
        await OpenWebuiProvisioner().sync_access()
