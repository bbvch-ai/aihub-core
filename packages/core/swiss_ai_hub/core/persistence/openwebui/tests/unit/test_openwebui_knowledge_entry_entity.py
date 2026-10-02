"""Every OpenWebUI id we issued keeps resolving to its collection, so a chat that referenced it is still understood
after the sync replaced or removed the entry; only one id per collection is listed at a time."""

import pytest
from mongoengine import connect, disconnect

from swiss_ai_hub.core.events.agent.user.knowledge_reference import KnowledgeReference
from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.openwebui.openwebui_knowledge_entry_entity import OpenWebuiKnowledgeEntryEntity

POLICIES = KnowledgeReference(database="hr", namespace="policies")
REPORTS = KnowledgeReference(database="hr", namespace="reports")


@pytest.fixture(autouse=True)
def clean_entries():
    connect(db=AIHubSettings().MONGO_MAIN_DB_NAME, host=MongoSettings().CONNECTION_STRING.get_secret_value())
    OpenWebuiKnowledgeEntryEntity.objects.delete()
    yield
    OpenWebuiKnowledgeEntryEntity.objects.delete()
    disconnect()


def test_a_replaced_entry_still_resolves_while_only_the_new_one_is_listed():
    OpenWebuiKnowledgeEntryEntity.record("k1", POLICIES)
    OpenWebuiKnowledgeEntryEntity.record("k2", POLICIES)

    assert [entry.openwebui_id for entry in OpenWebuiKnowledgeEntryEntity.current_entries()] == ["k2"]
    assert OpenWebuiKnowledgeEntryEntity.references_for(["k1", "k2"]) == [POLICIES, POLICIES]


def test_a_retired_entry_is_no_longer_listed_but_still_resolves():
    OpenWebuiKnowledgeEntryEntity.record("k1", POLICIES)
    OpenWebuiKnowledgeEntryEntity.record("k2", REPORTS)

    OpenWebuiKnowledgeEntryEntity.retire("k1")

    assert [entry.openwebui_id for entry in OpenWebuiKnowledgeEntryEntity.current_entries()] == ["k2"]
    assert OpenWebuiKnowledgeEntryEntity.references_for(["k1"]) == [POLICIES]


def test_an_id_we_never_issued_resolves_to_nothing():
    OpenWebuiKnowledgeEntryEntity.record("k1", POLICIES)

    assert OpenWebuiKnowledgeEntryEntity.references_for(["user-made", "k1"]) == [POLICIES]
