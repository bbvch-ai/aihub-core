import asyncio
import gc
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mongoengine import signals

from swiss_ai_hub.core.persistence.rag.datalake.entities.bucket_entity import BucketEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities.namespace_entity import NamespaceEntity
from swiss_ai_hub.core.persistence.rag.datalake.knowledge_change_hook import KnowledgeChangeHook


@pytest.fixture
def connected_hook():
    was_connected = KnowledgeChangeHook._connected
    KnowledgeChangeHook._connected = False
    provisioner = MagicMock(sync_knowledge=AsyncMock())
    KnowledgeChangeHook.connect(provisioner)
    yield provisioner
    for entity in (BucketEntity, NamespaceEntity):
        for sig in (signals.post_save, signals.post_delete):
            for receiver in list(sig.receivers_for(entity)):
                sig.disconnect(receiver, sender=entity)
    KnowledgeChangeHook._connected = was_connected
    KnowledgeChangeHook._provisioner = None
    KnowledgeChangeHook._debounce_task = None


def test_database_and_collection_changes_stay_subscribed(connected_hook):
    gc.collect()

    for entity in (BucketEntity, NamespaceEntity):
        assert list(signals.post_save.receivers_for(entity))
        assert list(signals.post_delete.receivers_for(entity))


@pytest.mark.asyncio
async def test_a_burst_of_changes_syncs_once(connected_hook):
    with patch("swiss_ai_hub.core.persistence.rag.datalake.knowledge_change_hook._DEBOUNCE_SECONDS", 0.05):
        for _ in range(3):
            signals.post_save.send(NamespaceEntity, document=MagicMock())
        await asyncio.sleep(0.2)

    connected_hook.sync_knowledge.assert_awaited_once()
