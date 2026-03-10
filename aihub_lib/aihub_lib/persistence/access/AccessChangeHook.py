import asyncio
import logging
from typing import Any, ClassVar

from mongoengine import signals

from aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner import OpenWebuiProvisioner
from aihub_lib.persistence.access.entities.RoleEntity import RoleEntity
from aihub_lib.persistence.access.entities.TenantEntity import TenantEntity
from aihub_lib.persistence.access.entities.UserTenantRoleEntity import UserTenantRoleEntity

logger = logging.getLogger(__name__)


class AccessChangeHook:
    _connected: ClassVar[bool] = False

    @classmethod
    def connect(cls) -> None:
        """Wires MongoEngine signals to sync OpenWebUI access on any access entity save/delete.

        Each signal fires an independent sync task. Bulk operations (e.g. assigning 50 users)
        will produce concurrent sync_access() calls. Consider adding debouncing if this becomes
        a problem at scale.
        """
        if cls._connected:
            return

        def _on_change(sender: type, document: Any, **kwargs: Any) -> None:
            logger.info("Access entity changed (%s), syncing OpenWebUI access", sender.__name__)
            asyncio.create_task(OpenWebuiProvisioner().sync_access())

        for entity_cls in [RoleEntity, TenantEntity, UserTenantRoleEntity]:
            signals.post_save.connect(_on_change, sender=entity_cls)
            signals.post_delete.connect(_on_change, sender=entity_cls)

        logger.info(
            "AccessChangeHook connected for %s",
            [cls.__name__ for cls in [RoleEntity, TenantEntity, UserTenantRoleEntity]],
        )
        cls._connected = True
