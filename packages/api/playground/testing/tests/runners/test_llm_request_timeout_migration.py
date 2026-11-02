"""The startup rewrite of LLM request timeouts saved at the old 600 s default (aihub-core-private#349).

The edit form stores the default it showed, so profiles saved before the default dropped to 300 s keep 600 s. The
rewrite must lower only LLM parameters (recognised by `temperature` next to `timeout`), leave embedding timeouts and
explicit values alone, and be a no-op on the next boot, since every API replica runs it on every start.
"""

from typing import Any

import pytest
from mongoengine import connect, disconnect, signals
from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity
from swiss_ai_hub.core.persistence.process.process_config_entity_document import ProcessConfigEntityDocument

from swiss_ai_hub.api.runners.lifetime.llm_request_timeout_migration import LLMRequestTimeoutMigration


def _llm_parameter(timeout: Any) -> dict[str, Any]:
    return {"temperature": 0.1, "max_retries": 3, "timeout": timeout}


class TestLowered:
    @pytest.mark.parametrize("old_default", [600, 600.0], ids=["int", "float"])
    def test_an_llm_parameter_at_the_old_default_is_lowered(self, old_default: float):
        assert LLMRequestTimeoutMigration.lowered(_llm_parameter(old_default)) == _llm_parameter(300.0)

    @pytest.mark.parametrize("timeout", [120.0, 900.0, 300.0, None], ids=["lower", "higher", "new default", "unset"])
    def test_any_other_timeout_is_left_alone(self, timeout: Any):
        assert LLMRequestTimeoutMigration.lowered(_llm_parameter(timeout)) == _llm_parameter(timeout)

    def test_an_embedding_timeout_without_temperature_is_left_alone(self):
        embedding_parameter = {"max_retries": 3, "timeout": 600.0}

        assert LLMRequestTimeoutMigration.lowered(embedding_parameter) == embedding_parameter

    def test_a_true_timeout_is_not_mistaken_for_a_number(self):
        assert LLMRequestTimeoutMigration.lowered(_llm_parameter(True)) == _llm_parameter(True)

    def test_nested_llm_parameters_are_lowered_wherever_a_blueprint_puts_them(self):
        config_data = {
            "llm": {"model_name": "chat/kimi", "default_parameter": _llm_parameter(600.0)},
            "steps": [{"llm": {"default_parameter": _llm_parameter(600)}}],
            "embedding": {"default_parameter": {"timeout": 600.0}},
        }

        assert LLMRequestTimeoutMigration.lowered(config_data) == {
            "llm": {"model_name": "chat/kimi", "default_parameter": _llm_parameter(300.0)},
            "steps": [{"llm": {"default_parameter": _llm_parameter(300.0)}}],
            "embedding": {"default_parameter": {"timeout": 600.0}},
        }


@pytest.fixture
def mongo_connection():
    client = connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
    )
    yield client
    disconnect()


@pytest.fixture
def clean_configs(mongo_connection):
    # Muted for the same reason as in `test_empty_namespace_scope_migration`: an earlier test may have connected
    # `AgentConfigChangeHook`, whose receiver schedules an asyncio task, and these tests run without a loop.
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


@pytest.mark.usefixtures("clean_configs")
class TestRun:
    def test_stored_configs_at_the_old_default_are_rewritten_and_reported(self):
        stale_agent = _agent("stale", {"llm": {"default_parameter": _llm_parameter(600.0)}})
        stale_process = _process("stale", {"llm": {"default_parameter": _llm_parameter(600.0)}})
        _agent("explicit", {"llm": {"default_parameter": _llm_parameter(120.0)}})

        migrated = LLMRequestTimeoutMigration.run()

        assert migrated == ["agent RAGAgent/stale", "process ReviewProcess/stale"]
        stale_agent.reload()
        stale_process.reload()
        assert stale_agent.config_data["llm"]["default_parameter"]["timeout"] == 300.0
        assert stale_process.config_data["llm"]["default_parameter"]["timeout"] == 300.0

    def test_a_second_boot_rewrites_nothing(self):
        _agent("stale", {"llm": {"default_parameter": _llm_parameter(600.0)}})
        LLMRequestTimeoutMigration.run()

        assert LLMRequestTimeoutMigration.run() == []
