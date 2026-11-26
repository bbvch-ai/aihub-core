"""What the Beanie port of agent classes promises about storage (#1962).

The MongoEngine document ran `strict: False`, so stored classes may carry fields the model does not declare, and a
rediscovery must not drop them. Discovery times stay naive local time, the clock the discovery rounds are compared on.
"""

from datetime import datetime

import pytest
from pymongo.asynchronous.database import AsyncDatabase

from swiss_ai_hub.core.agents.visualizers.types.workflow_graph import WorkflowGraph
from swiss_ai_hub.core.events.agent.discovery.agent_class_discovery_response_event import (
    AgentClassDiscoveryResponseEvent,
)
from swiss_ai_hub.core.events.discovery.event_specs import EventSpecs
from swiss_ai_hub.core.form.config_specs import ConfigSpecs
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.persistence.agents.agent_class_entity import AgentClassEntity

pytestmark = pytest.mark.beanie


def _discovery(icon: str = "mage:robot") -> AgentClassDiscoveryResponseEvent:
    start = EventSpecs(event_name="StartEvent", event_schema={"$defs": {}, "type": "object"}, event_parents=[])
    return AgentClassDiscoveryResponseEvent(
        agent_class="RAGAgent",
        name=LocaleString(en="RAG"),
        description=LocaleString(en="Answers from documents"),
        icon=icon,
        form=[],
        agent_config_specs=ConfigSpecs(config_class="RAGConfig", config_schema={"$defs": {}}),
        is_conversational=True,
        is_schedulable=False,
        start_events=[start],
        stop_events=[start],
        hitl_request_events=[],
        hitl_response_events=[],
        network_graph=WorkflowGraph(nodes=[], links=[]),
    )


async def test_a_rediscovery_keeps_a_field_the_model_does_not_declare(beanie_test_database: AsyncDatabase):
    entity = await AgentClassEntity.create_or_update(_discovery())
    await beanie_test_database["agent_classes"].update_one({"_id": entity.id}, {"$set": {"legacy_flag": True}})

    await AgentClassEntity.create_or_update(_discovery(icon="mage:book-open"))

    stored = await beanie_test_database["agent_classes"].find_one({"_id": entity.id})
    assert stored["legacy_flag"] is True
    assert stored["icon"] == "mage:book-open"


async def test_schemas_with_dollar_keys_are_stored_as_json_strings(beanie_test_database: AsyncDatabase):
    """MongoDB rejects keys starting with '$', which every non-trivial JSON schema has."""
    entity = await AgentClassEntity.create_or_update(_discovery())

    stored = await beanie_test_database["agent_classes"].find_one({"_id": entity.id})

    assert isinstance(stored["start_events"][0]["event_schema_json"], str)
    assert isinstance(stored["agent_config_specs"]["config_schema_json"], str)
    reloaded = await AgentClassEntity.get_by_agent_class("RAGAgent")
    assert reloaded.start_events[0].event_schema == {"$defs": {}, "type": "object"}
    assert reloaded.agent_config_specs.to_specs().config_schema == {"$defs": {}}


async def test_discovery_times_stay_naive_local_time(beanie_test_database: AsyncDatabase):
    before = datetime.now()
    entity = await AgentClassEntity.create_or_update(_discovery())

    stored = await beanie_test_database["agent_classes"].find_one({"_id": entity.id})

    assert stored["last_discovered"].tzinfo is None
    assert abs((stored["last_discovered"] - before).total_seconds()) < 60


async def test_a_class_stored_without_last_discovered_reads_as_offline(beanie_test_database: AsyncDatabase):
    entity = await AgentClassEntity.create_or_update(_discovery())
    await beanie_test_database["agent_classes"].update_one({"_id": entity.id}, {"$unset": {"last_discovered": ""}})

    reloaded = await AgentClassEntity.get_by_agent_class("RAGAgent")

    assert reloaded.is_online_since(datetime.now()) is False
