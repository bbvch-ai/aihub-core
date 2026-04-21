from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, ClassVar

from mongoengine import signals

from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity

if TYPE_CHECKING:
    from swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner import OpenWebuiProvisioner

logger = logging.getLogger(__name__)

_DEBOUNCE_SECONDS = 2.0


class AccessChangeHook:
    _connected: ClassVar[bool] = False
    _debounce_task: ClassVar[asyncio.Task | None] = None
    _provisioner: ClassVar[OpenWebuiProvisioner | None] = None

    @classmethod
    def connect(cls, provisioner: OpenWebuiProvisioner) -> None:
        """Wires MongoEngine signals to sync OpenWebUI access on any access entity save/delete.

        Rapid mutations are debounced: only the last change in a 2-second quiet window triggers sync.
        """
        if cls._connected:
            return

        cls._provisioner = provisioner

        def _on_change(sender: type, document: Any, **kwargs: Any) -> None:
            logger.info("Access entity changed (%s), scheduling OpenWebUI sync", sender.__name__)
            cls._schedule_sync()

        for entity_cls in [RoleEntity, TenantMetadataEntity, UserTenantRoleEntity]:
            signals.post_save.connect(_on_change, sender=entity_cls)
            signals.post_delete.connect(_on_change, sender=entity_cls)

        logger.info(
            "AccessChangeHook connected for %s",
            [cls.__name__ for cls in [RoleEntity, TenantMetadataEntity, UserTenantRoleEntity]],
        )
        cls._connected = True

    @classmethod
    def notify(cls) -> None:
        """Explicitly schedule an OpenWebUI sync from outside the signal system."""
        if not cls._connected:
            return
        logger.info("Explicit access change notification, scheduling OpenWebUI sync")
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
