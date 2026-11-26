"""The startup carry-over of mail categories saved before collections became (database, collection) pairs (#299).

Read at runtime, the old keys narrowed a category an admin had switched to "every collection" back to its old
collection, because the edit form round-trips keys it does not render. The rewrite must carry over only the categories
that never held the pair key, respect every explicit choice, `null` included, delete the old keys everywhere, and be a
no-op on the next boot, since every API replica runs it on every start.
"""

from typing import Any

import pytest
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument

from swiss_ai_hub.api.runners.lifetime.pre_pair_knowledge_collection_migration import (
    PrePairKnowledgeCollectionMigration,
)

pytestmark = pytest.mark.beanie

SUPPORT_PAIR = {"bucket_name": "support-kb", "namespace_name": "support"}


async def _agent(classification: dict[str, Any]) -> AgentConfigEntityDocument:
    return await AgentConfigEntityDocument(
        agent_class="EmailClassificationAgent",
        agent_id="mailbox",
        name=LocaleString(en="mailbox"),
        description=LocaleString(en="mailbox profile"),
        icon="meteor-icons:robot",
        config_data={"imap": {"host": "imap.example.com"}, "classification": classification},
    ).insert()


def _category(name: str, **knowledge: Any) -> dict[str, Any]:
    return {"category": name, "imap_folder": name, "description": f"{name} mail", "draft_reply": True} | knowledge


async def _classification(agent: AgentConfigEntityDocument) -> dict[str, Any]:
    return (await AgentConfigEntityDocument.get(agent.id)).config_data["classification"]


async def test_a_category_without_the_pair_key_is_carried_over_to_pairs():
    agent = await _agent(
        {"knowledge_databases": ["support-kb"], "categories": [_category("support", knowledge_namespace="support")]}
    )

    assert await PrePairKnowledgeCollectionMigration.run() == ["agent EmailClassificationAgent/mailbox"]

    assert await _classification(agent) == {"categories": [_category("support", knowledge_namespaces=[SUPPORT_PAIR])]}


async def test_every_database_is_paired_because_the_old_shape_did_not_say_which_held_the_collection():
    agent = await _agent(
        {
            "knowledge_databases": ["support-kb", "archive"],
            "categories": [_category("support", knowledge_namespace="support")],
        }
    )

    await PrePairKnowledgeCollectionMigration.run()

    assert (await _classification(agent))["categories"][0]["knowledge_namespaces"] == [
        SUPPORT_PAIR,
        {"bucket_name": "archive", "namespace_name": "support"},
    ]


async def test_categories_stored_in_formkits_numbered_dict_shape_are_carried_over():
    """The runtime reads this shape as a list, so the old carry-over saw these categories and so must this one."""
    agent = await _agent(
        {
            "knowledge_databases": ["support-kb"],
            "categories": {
                "0": _category("support", knowledge_namespace="support"),
                "1": _category("info", knowledge_namespaces=None),
            },
        }
    )

    assert await PrePairKnowledgeCollectionMigration.run() == ["agent EmailClassificationAgent/mailbox"]

    assert await _classification(agent) == {
        "categories": [
            _category("support", knowledge_namespaces=[SUPPORT_PAIR]),
            _category("info", knowledge_namespaces=None),
        ]
    }


async def test_a_selection_switched_off_stays_off():
    """The #299 case: the pair-aware form saved `null`, yet the old keys narrowed the category back at runtime."""
    agent = await _agent(
        {
            "knowledge_databases": ["support-kb"],
            "categories": [_category("support", knowledge_namespace="support", knowledge_namespaces=None)],
        }
    )

    await PrePairKnowledgeCollectionMigration.run()

    assert await _classification(agent) == {"categories": [_category("support", knowledge_namespaces=None)]}


async def test_an_explicit_selection_is_kept_and_only_the_old_keys_go():
    chosen = [{"bucket_name": "handbook", "namespace_name": "hr"}]
    agent = await _agent(
        {
            "knowledge_databases": ["support-kb"],
            "categories": [_category("support", knowledge_namespace="support", knowledge_namespaces=chosen)],
        }
    )

    await PrePairKnowledgeCollectionMigration.run()

    assert await _classification(agent) == {"categories": [_category("support", knowledge_namespaces=chosen)]}


async def test_a_category_that_never_named_a_collection_is_left_unset():
    agent = await _agent({"knowledge_databases": ["support-kb"], "categories": [_category("invoice")]})

    await PrePairKnowledgeCollectionMigration.run()

    assert await _classification(agent) == {"categories": [_category("invoice")]}


async def test_a_stray_collection_key_without_databases_is_removed():
    agent = await _agent({"categories": [_category("support", knowledge_namespace="support")]})

    await PrePairKnowledgeCollectionMigration.run()

    assert await _classification(agent) == {"categories": [_category("support")]}


async def test_a_profile_in_the_current_shape_is_left_alone():
    classification = {
        "categories": [
            _category("support", knowledge_namespaces=[SUPPORT_PAIR]),
            _category("info", knowledge_namespaces=None),
        ]
    }
    agent = await _agent(classification)

    assert await PrePairKnowledgeCollectionMigration.run() == []

    assert await _classification(agent) == classification


async def test_a_second_run_changes_nothing():
    """Every API replica runs this on every boot, so the steady state must be a pass that writes nothing."""
    await _agent(
        {"knowledge_databases": ["support-kb"], "categories": [_category("support", knowledge_namespace="support")]}
    )
    await PrePairKnowledgeCollectionMigration.run()

    assert await PrePairKnowledgeCollectionMigration.run() == []


async def test_a_config_saved_since_it_was_read_is_not_overwritten():
    """Another replica, or an admin, may save the profile between this replica's read and write."""
    agent = await _agent(
        {"knowledge_databases": ["support-kb"], "categories": [_category("support", knowledge_namespace="support")]}
    )
    stale_config = agent.config_data
    agent.config_data = {"classification": {"categories": [_category("support", knowledge_namespaces=None)]}}
    await agent.save_changes()

    replaced = await AgentConfigEntityDocument.replace_config_data_if_unchanged(
        agent.id, stale_config, PrePairKnowledgeCollectionMigration.rewritten(stale_config)
    )

    assert replaced is False
    assert await _classification(agent) == {"categories": [_category("support", knowledge_namespaces=None)]}
