from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, ClassVar

from mongoengine import signals

from swiss_ai_hub.core.persistence.rag.datalake.entities.bucket_entity import BucketEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities.namespace_entity import NamespaceEntity

if TYPE_CHECKING:
    from swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner import OpenWebuiProvisioner

logger = logging.getLogger(__name__)

_DEBOUNCE_SECONDS = 2.0


class KnowledgeChangeHook:
    """Reflects knowledge database and collection changes into the collections users reference with `#`.

    A created, renamed or deleted collection otherwise only shows up in OpenWebUI on the next periodic reconcile.
    Collections a pipeline creates, and bulk updates, fire no signal here; the periodic reconcile covers those.
    """

    _connected: ClassVar[bool] = False
    _debounce_task: ClassVar[asyncio.Task | None] = None
    _provisioner: ClassVar[OpenWebuiProvisioner | None] = None

    @classmethod
    def connect(cls, provisioner: OpenWebuiProvisioner) -> None:
        """Wires MongoEngine signals to sync OpenWebUI knowledge entries; rapid changes are debounced."""
        if cls._connected:
            return

        cls._provisioner = provisioner

        def _on_change(sender: type, document: Any, **kwargs: Any) -> None:
            logger.info("Knowledge changed (%s), scheduling OpenWebUI knowledge sync", sender.__name__)
            cls._schedule_sync()

        # weak=False: the closure has no other strong reference, so a weak one would be collected at once.
        for entity in (BucketEntity, NamespaceEntity):
            signals.post_save.connect(_on_change, sender=entity, weak=False)
            signals.post_delete.connect(_on_change, sender=entity, weak=False)

        logger.info("KnowledgeChangeHook connected")
        cls._connected = True

    @classmethod
    def _schedule_sync(cls) -> None:
        if cls._debounce_task and not cls._debounce_task.done():
            cls._debounce_task.cancel()
        cls._debounce_task = asyncio.create_task(cls._debounced_sync())

    @classmethod
    async def _debounced_sync(cls) -> None:
        await asyncio.sleep(_DEBOUNCE_SECONDS)
        await cls._provisioner.sync_knowledge()
