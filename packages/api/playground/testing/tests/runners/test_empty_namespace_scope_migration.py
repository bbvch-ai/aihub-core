"""The startup rewrite of retriever scopes saved empty before #1603 made an empty scope invalid (#1836).

Before #1603 an empty `index_namespaces` searched the whole collection; after it, every run of such an agent aborts.
The rewrite must give those configs the all-namespaces scope they were saved with, leave every explicit scope alone,
and be a no-op on the next boot, since every API replica runs it on every start.
"""

from typing import Any

import pytest
from mongoengine import connect, disconnect, signals
from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity
from swiss_ai_hub.core.persistence.process.process_config_entity_document import ProcessConfigEntityDocument

from swiss_ai_hub.api.runners.lifetime.empty_namespace_scope_migration import EmptyNamespaceScopeMigration

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
def clean_configs(mongo_connection):
    # Muted because an earlier test in the suite may have started the API lifespan, which connects
    # `AgentConfigChangeHook`; its receiver schedules an asyncio task and these tests run without a loop.
    # The migration itself writes through `update_one`, which sends no document signals either way.
    with signals.post_save.muted(), signals.post_delete.muted():
        AgentConfigEntityDocument.objects.delete()
        ProcessConfigEntityDocument.objects.delete()
        yield
        AgentConfigEntityDocument.objects.delete()
        ProcessConfigEntityDocument.objects.delete()


def _agent(agent_id: str, config_data: dict[str, Any]) -> AgentConfigEntityDocument:
    return AgentConfigEntityDocument(
        agent_class="RAGAgent",
        agent_id=agent_id,
        name=LocaleStringEntity(en=agent_id),
        description=LocaleStringEntity(en=f"{agent_id} profile"),
        icon="meteor-icons:robot",
        config_data=config_data,
    ).save()


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
def test_an_empty_scope_in_a_repeater_list_reads_every_namespace(mongo_connection, vector_store: dict[str, Any]):
    agent = _agent("hr", {"system_prompt": "Be kind.", "retrievers": [_retriever(vector_store)]})

    assert EmptyNamespaceScopeMigration.run() == ["agent RAGAgent/hr"]

    assert agent.reload().config_data == {"system_prompt": "Be kind.", "retrievers": [_retriever(WIDENED)]}


def test_the_numbered_dict_shape_is_rewritten_too(mongo_connection):
    agent = _agent("hr", {"retrievers": {"0": _retriever({"collection_name": "handbook", "index_namespaces": []})}})

    EmptyNamespaceScopeMigration.run()

    assert agent.reload().config_data == {"retrievers": {"0": _retriever(WIDENED)}}


def test_a_retriever_nested_in_a_group_is_rewritten(mongo_connection):
    agent = _agent("hr", {"retriever": _retriever({"collection_name": "handbook", "index_namespaces": []})})

    EmptyNamespaceScopeMigration.run()

    assert agent.reload().config_data == {"retriever": _retriever(WIDENED)}


def test_only_the_empty_row_changes(mongo_connection):
    named = {"collection_name": "legal", "index_namespaces": ["contracts"], "all_namespaces": False}
    agent = _agent(
        "hr",
        {"retrievers": [_retriever(named), _retriever({"collection_name": "handbook", "index_namespaces": []})]},
    )

    EmptyNamespaceScopeMigration.run()

    assert agent.reload().config_data == {"retrievers": [_retriever(named), _retriever(WIDENED)]}


@pytest.mark.parametrize(
    "vector_store",
    [
        {"collection_name": "handbook", "index_namespaces": ["policies"], "all_namespaces": False},
        {"collection_name": "handbook", "index_namespaces": [], "all_namespaces": True},
    ],
    ids=["named namespaces", "all namespaces"],
)
def test_an_explicit_scope_is_left_alone(mongo_connection, vector_store: dict[str, Any]):
    agent = _agent("hr", {"retrievers": [_retriever(vector_store)]})

    assert EmptyNamespaceScopeMigration.run() == []

    assert agent.reload().config_data == {"retrievers": [_retriever(vector_store)]}


def test_process_configs_are_covered(mongo_connection):
    process = _process("review", {"retriever": _retriever({"collection_name": "handbook", "index_namespaces": []})})

    assert EmptyNamespaceScopeMigration.run() == ["process ReviewProcess/review"]

    assert process.reload().config_data == {"retriever": _retriever(WIDENED)}


def test_a_second_run_changes_nothing(mongo_connection):
    """Every API replica runs this on every boot, so the steady state must be a pass that writes nothing."""
    _agent("hr", {"retrievers": [_retriever({"collection_name": "handbook", "index_namespaces": []})]})
    EmptyNamespaceScopeMigration.run()

    assert EmptyNamespaceScopeMigration.run() == []


def test_a_config_saved_since_it_was_read_is_not_overwritten(mongo_connection):
    """Another replica, or an admin, may save the profile between this replica's read and write."""
    agent = _agent("hr", {"retrievers": [_retriever({"collection_name": "handbook", "index_namespaces": []})]})
    stale_config = agent.config_data
    agent.config_data = {"retrievers": [_retriever({"collection_name": "handbook", "index_namespaces": ["hr"]})]}
    agent.save()

    replaced = AgentConfigEntityDocument.replace_config_data_if_unchanged(
        agent.pk, stale_config, EmptyNamespaceScopeMigration.widened(stale_config)
    )

    assert replaced is False
    assert agent.reload().config_data["retrievers"][0]["vector_store"]["index_namespaces"] == ["hr"]
