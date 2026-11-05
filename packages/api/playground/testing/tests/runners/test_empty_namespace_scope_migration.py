"""The startup rewrite of retriever scopes saved empty before #1603 made an empty scope invalid (#1836).

Before #1603 an empty `index_namespaces` searched the whole collection; after it, every run of such an agent aborts.
The rewrite must give those configs the all-namespaces scope they were saved with, leave every explicit scope alone,
and be a no-op on the next boot, since every API replica runs it on every start.
"""

from typing import Any

import pytest
from mongoengine import connect, disconnect, signals
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity
from swiss_ai_hub.core.persistence.process.process_config_entity_document import ProcessConfigEntityDocument

from swiss_ai_hub.api.runners.lifetime.empty_namespace_scope_migration import EmptyNamespaceScopeMigration

pytestmark = pytest.mark.beanie

WIDENED = {"collection_name": "handbook", "index_namespaces": [], "all_namespaces": True}


@pytest.fixture
def mongo_connection():
    client = connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
    )
    yield client
    disconnect()


@pytest.fixture(autouse=True)
def clean_process_configs(mongo_connection):
    # Process configs stay on MongoEngine. Muted because an earlier test in the suite may have started the API
    # lifespan, which connects their change hook; its receiver schedules an asyncio task.
    with signals.post_save.muted(), signals.post_delete.muted():
        ProcessConfigEntityDocument.objects.delete()
        yield
        ProcessConfigEntityDocument.objects.delete()


async def _agent(agent_id: str, config_data: dict[str, Any]) -> AgentConfigEntityDocument:
    return await AgentConfigEntityDocument(
        agent_class="RAGAgent",
        agent_id=agent_id,
        name=LocaleString(en=agent_id),
        description=LocaleString(en=f"{agent_id} profile"),
        icon="meteor-icons:robot",
        config_data=config_data,
    ).insert()


async def _stored_config_data(agent: AgentConfigEntityDocument) -> dict[str, Any]:
    return (await AgentConfigEntityDocument.get(agent.id)).config_data


def _process(process_id: str, config_data: dict[str, Any]) -> ProcessConfigEntityDocument:
    return ProcessConfigEntityDocument(
        process_class="ReviewProcess",
        process_id=process_id,
        name=LocaleStringEntity(en=process_id),
        description=LocaleStringEntity(en=f"{process_id} instance"),
        icon="meteor-icons:robot",
        config_data=config_data,
    ).save()


def _retriever(vector_store: dict[str, Any]) -> dict[str, Any]:
    return {"retrieve_k": 5, "vector_store": vector_store}


@pytest.mark.parametrize(
    "vector_store",
    [
        {"collection_name": "handbook", "index_namespaces": [], "all_namespaces": False},
        {"collection_name": "handbook", "index_namespaces": []},
        {"collection_name": "handbook", "index_namespaces": None, "all_namespaces": False},
        {"collection_name": "handbook"},
    ],
    ids=["empty list", "all_namespaces missing", "null list", "no scope keys"],
)
async def test_an_empty_scope_in_a_repeater_list_reads_every_namespace(mongo_connection, vector_store: dict[str, Any]):
    agent = await _agent("hr", {"system_prompt": "Be kind.", "retrievers": [_retriever(vector_store)]})

    assert await EmptyNamespaceScopeMigration.run() == ["agent RAGAgent/hr"]

    assert await _stored_config_data(agent) == {"system_prompt": "Be kind.", "retrievers": [_retriever(WIDENED)]}


async def test_the_numbered_dict_shape_is_rewritten_too(mongo_connection):
    agent = await _agent(
        "hr", {"retrievers": {"0": _retriever({"collection_name": "handbook", "index_namespaces": []})}}
    )

    await EmptyNamespaceScopeMigration.run()

    assert await _stored_config_data(agent) == {"retrievers": {"0": _retriever(WIDENED)}}


async def test_a_retriever_nested_in_a_group_is_rewritten(mongo_connection):
    agent = await _agent("hr", {"retriever": _retriever({"collection_name": "handbook", "index_namespaces": []})})

    await EmptyNamespaceScopeMigration.run()

    assert await _stored_config_data(agent) == {"retriever": _retriever(WIDENED)}


async def test_only_the_empty_row_changes(mongo_connection):
    named = {"collection_name": "legal", "index_namespaces": ["contracts"], "all_namespaces": False}
    agent = await _agent(
        "hr",
        {"retrievers": [_retriever(named), _retriever({"collection_name": "handbook", "index_namespaces": []})]},
    )

    await EmptyNamespaceScopeMigration.run()

    assert await _stored_config_data(agent) == {"retrievers": [_retriever(named), _retriever(WIDENED)]}


@pytest.mark.parametrize(
    "vector_store",
    [
        {"collection_name": "handbook", "index_namespaces": ["policies"], "all_namespaces": False},
        {"collection_name": "handbook", "index_namespaces": [], "all_namespaces": True},
    ],
    ids=["named namespaces", "all namespaces"],
)
async def test_an_explicit_scope_is_left_alone(mongo_connection, vector_store: dict[str, Any]):
    agent = await _agent("hr", {"retrievers": [_retriever(vector_store)]})

    assert await EmptyNamespaceScopeMigration.run() == []

    assert await _stored_config_data(agent) == {"retrievers": [_retriever(vector_store)]}


async def test_process_configs_are_covered(mongo_connection):
    process = _process("review", {"retriever": _retriever({"collection_name": "handbook", "index_namespaces": []})})

    assert await EmptyNamespaceScopeMigration.run() == ["process ReviewProcess/review"]

    assert process.reload().config_data == {"retriever": _retriever(WIDENED)}


async def test_a_second_run_changes_nothing(mongo_connection):
    """Every API replica runs this on every boot, so the steady state must be a pass that writes nothing."""
    await _agent("hr", {"retrievers": [_retriever({"collection_name": "handbook", "index_namespaces": []})]})
    await EmptyNamespaceScopeMigration.run()

    assert await EmptyNamespaceScopeMigration.run() == []


async def test_a_config_saved_since_it_was_read_is_not_overwritten(mongo_connection):
    """Another replica, or an admin, may save the profile between this replica's read and write."""
    agent = await _agent("hr", {"retrievers": [_retriever({"collection_name": "handbook", "index_namespaces": []})]})
    stale_config = agent.config_data
    agent.config_data = {"retrievers": [_retriever({"collection_name": "handbook", "index_namespaces": ["hr"]})]}
    await agent.save_changes()

    replaced = await AgentConfigEntityDocument.replace_config_data_if_unchanged(
        agent.id, stale_config, EmptyNamespaceScopeMigration.widened(stale_config)
    )

    assert replaced is False
    assert (await _stored_config_data(agent))["retrievers"][0]["vector_store"]["index_namespaces"] == ["hr"]
