"""The startup carry-over of mail categories saved before collections became (database, collection) pairs (#299).

Read at runtime, the old keys narrowed a category an admin had switched to "every collection" back to its old
collection, because the edit form round-trips keys it does not render. The rewrite must carry over only the categories
that never held the pair key, respect every explicit choice, `null` included, delete the old keys everywhere, and be a
no-op on the next boot, since every API replica runs it on every start.
"""

from typing import Any

import pytest
from mongoengine import connect, disconnect, signals
from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity

from swiss_ai_hub.api.runners.lifetime.pre_pair_knowledge_collection_migration import (
    PrePairKnowledgeCollectionMigration,
)

SUPPORT_PAIR = {"bucket_name": "support-kb", "namespace_name": "support"}


@pytest.fixture
def mongo_connection():
    client = connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
    )
    yield client
    disconnect()


@pytest.fixture(autouse=True)
def clean_configs(mongo_connection):
    # Muted for the same reason as in test_empty_namespace_scope_migration: an earlier test may have connected
    # `AgentConfigChangeHook`, whose receiver needs an event loop these tests do not run.
    with signals.post_save.muted(), signals.post_delete.muted():
        AgentConfigEntityDocument.objects.delete()
        yield
        AgentConfigEntityDocument.objects.delete()


def _agent(classification: dict[str, Any]) -> AgentConfigEntityDocument:
    return AgentConfigEntityDocument(
        agent_class="EmailClassificationAgent",
        agent_id="mailbox",
        name=LocaleStringEntity(en="mailbox"),
        description=LocaleStringEntity(en="mailbox profile"),
        icon="meteor-icons:robot",
        config_data={"imap": {"host": "imap.example.com"}, "classification": classification},
    ).save()


def _category(name: str, **knowledge: Any) -> dict[str, Any]:
    return {"category": name, "imap_folder": name, "description": f"{name} mail", "draft_reply": True} | knowledge


def _classification(agent: AgentConfigEntityDocument) -> dict[str, Any]:
    return agent.reload().config_data["classification"]


def test_a_category_without_the_pair_key_is_carried_over_to_pairs(mongo_connection):
    agent = _agent(
        {"knowledge_databases": ["support-kb"], "categories": [_category("support", knowledge_namespace="support")]}
    )

    assert PrePairKnowledgeCollectionMigration.run() == ["agent EmailClassificationAgent/mailbox"]

    assert _classification(agent) == {"categories": [_category("support", knowledge_namespaces=[SUPPORT_PAIR])]}


def test_every_database_is_paired_because_the_old_shape_did_not_say_which_held_the_collection(mongo_connection):
    agent = _agent(
        {
            "knowledge_databases": ["support-kb", "archive"],
            "categories": [_category("support", knowledge_namespace="support")],
        }
    )

    PrePairKnowledgeCollectionMigration.run()

    assert _classification(agent)["categories"][0]["knowledge_namespaces"] == [
        SUPPORT_PAIR,
        {"bucket_name": "archive", "namespace_name": "support"},
    ]


def test_categories_stored_in_formkits_numbered_dict_shape_are_carried_over(mongo_connection):
    """The runtime reads this shape as a list, so the old carry-over saw these categories and so must this one."""
    agent = _agent(
        {
            "knowledge_databases": ["support-kb"],
            "categories": {
                "0": _category("support", knowledge_namespace="support"),
                "1": _category("info", knowledge_namespaces=None),
            },
        }
    )

    assert PrePairKnowledgeCollectionMigration.run() == ["agent EmailClassificationAgent/mailbox"]

    assert _classification(agent) == {
        "categories": [
            _category("support", knowledge_namespaces=[SUPPORT_PAIR]),
            _category("info", knowledge_namespaces=None),
        ]
    }


def test_a_selection_switched_off_stays_off(mongo_connection):
    """The #299 case: the pair-aware form saved `null`, yet the old keys narrowed the category back at runtime."""
    agent = _agent(
        {
            "knowledge_databases": ["support-kb"],
            "categories": [_category("support", knowledge_namespace="support", knowledge_namespaces=None)],
        }
    )

    PrePairKnowledgeCollectionMigration.run()

    assert _classification(agent) == {"categories": [_category("support", knowledge_namespaces=None)]}


def test_an_explicit_selection_is_kept_and_only_the_old_keys_go(mongo_connection):
    chosen = [{"bucket_name": "handbook", "namespace_name": "hr"}]
    agent = _agent(
        {
            "knowledge_databases": ["support-kb"],
            "categories": [_category("support", knowledge_namespace="support", knowledge_namespaces=chosen)],
        }
    )

    PrePairKnowledgeCollectionMigration.run()

    assert _classification(agent) == {"categories": [_category("support", knowledge_namespaces=chosen)]}


def test_a_category_that_never_named_a_collection_is_left_unset(mongo_connection):
    agent = _agent({"knowledge_databases": ["support-kb"], "categories": [_category("invoice")]})

    PrePairKnowledgeCollectionMigration.run()

    assert _classification(agent) == {"categories": [_category("invoice")]}


def test_a_stray_collection_key_without_databases_is_removed(mongo_connection):
    agent = _agent({"categories": [_category("support", knowledge_namespace="support")]})

    PrePairKnowledgeCollectionMigration.run()

    assert _classification(agent) == {"categories": [_category("support")]}


def test_a_profile_in_the_current_shape_is_left_alone(mongo_connection):
    classification = {
        "categories": [
            _category("support", knowledge_namespaces=[SUPPORT_PAIR]),
            _category("info", knowledge_namespaces=None),
        ]
    }
    agent = _agent(classification)

    assert PrePairKnowledgeCollectionMigration.run() == []

    assert _classification(agent) == classification


def test_a_second_run_changes_nothing(mongo_connection):
    """Every API replica runs this on every boot, so the steady state must be a pass that writes nothing."""
    _agent({"knowledge_databases": ["support-kb"], "categories": [_category("support", knowledge_namespace="support")]})
    PrePairKnowledgeCollectionMigration.run()

    assert PrePairKnowledgeCollectionMigration.run() == []


def test_a_config_saved_since_it_was_read_is_not_overwritten(mongo_connection):
    """Another replica, or an admin, may save the profile between this replica's read and write."""
    agent = _agent(
        {"knowledge_databases": ["support-kb"], "categories": [_category("support", knowledge_namespace="support")]}
    )
    stale_config = agent.config_data
    agent.config_data = {"classification": {"categories": [_category("support", knowledge_namespaces=None)]}}
    agent.save()

    replaced = AgentConfigEntityDocument.replace_config_data_if_unchanged(
        agent.pk, stale_config, PrePairKnowledgeCollectionMigration.rewritten(stale_config)
    )

    assert replaced is False
    assert _classification(agent) == {"categories": [_category("support", knowledge_namespaces=None)]}
