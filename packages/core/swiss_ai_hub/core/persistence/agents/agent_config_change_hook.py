from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, ClassVar

from mongoengine import signals

from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument

if TYPE_CHECKING:
    from swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner import OpenWebuiProvisioner

logger = logging.getLogger(__name__)

_DEBOUNCE_SECONDS = 2.0


class AgentConfigChangeHook:
    """Reflects agent-config mutations into OpenWebUI workspace models immediately.

    Without this, a created/renamed/deleted agent only appears in (or disappears from) the
    OpenWebUI model picker on the next periodic discovery cycle. Wiring the config entity's
    save/delete signals to a debounced ``sync_known_agents`` closes that lag window.
    """

    _connected: ClassVar[bool] = False
    _debounce_task: ClassVar[asyncio.Task | None] = None
    _provisioner: ClassVar[OpenWebuiProvisioner | None] = None

    @classmethod
    def connect(cls, provisioner: OpenWebuiProvisioner) -> None:
        """Wires MongoEngine signals to sync OpenWebUI agents on any config save/delete.

        Rapid mutations are debounced: only the last change in a 2-second quiet window triggers sync.
        """
        if cls._connected:
            return

        cls._provisioner = provisioner

        def _on_change(sender: type, document: Any, **kwargs: Any) -> None:
            logger.info("Agent config changed (%s), scheduling OpenWebUI agent sync", sender.__name__)
            cls._schedule_sync()

        # weak=False is required: ``_on_change`` is a local closure with no other strong reference, so
        # blinker's default weak ref would let it be garbage-collected the moment ``connect`` returns,
        # silently dropping the subscription so no config change ever triggers an OpenWebUI re-sync.
        signals.post_save.connect(_on_change, sender=AgentConfigEntityDocument, weak=False)
        signals.post_delete.connect(_on_change, sender=AgentConfigEntityDocument, weak=False)

        logger.info("AgentConfigChangeHook connected for %s", AgentConfigEntityDocument.__name__)
        cls._connected = True

    @classmethod
    def notify(cls) -> None:
        """Explicitly schedule an OpenWebUI agent sync from outside the signal system."""
        if not cls._connected:
            return
        logger.info("Explicit agent config change notification, scheduling OpenWebUI agent sync")
        cls._schedule_sync()

    @classmethod
    def _schedule_sync(cls) -> None:
        if cls._debounce_task and not cls._debounce_task.done():
            cls._debounce_task.cancel()
        cls._debounce_task = asyncio.create_task(cls._debounced_sync())

    @classmethod
    async def _debounced_sync(cls) -> None:
        await asyncio.sleep(_DEBOUNCE_SECONDS)
        await cls._provisioner.sync_known_agents()
