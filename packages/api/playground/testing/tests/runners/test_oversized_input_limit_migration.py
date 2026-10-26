"""The startup unset of input-token limits above what the model allows.

Profiles were created with a pre-filled 128,000 whatever the model, and saves now reject a limit above the field's
bound (85% of the window), so such a profile on a smaller model could not be saved at all. The rewrite must unset
exactly those limits, read the bound from the announced form, keep every limit within it, leave a profile alone when
its window or its form is unknown, and be a no-op on the next boot, since every API replica runs it on every start.
"""

from typing import Annotated, Any
from unittest.mock import patch

import pytest
from mongoengine import connect, disconnect, signals
from pydantic import Field
from swiss_ai_hub.core.form import ALL_FORM_OPTIONS, Form, ModelBoundInputNumber  # noqa: F401 — rebuilds Group
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.agents.agent_class_entity import AgentClassEntity
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity

from swiss_ai_hub.api.runners.lifetime.oversized_input_limit_migration import OversizedInputLimitMigration

SMALL_MODEL = "text-generation/small"
UNKNOWN_MODEL = "text-generation/unknown"
WINDOWS = {SMALL_MODEL: 65536}
BOUND = int(65536 * 0.85)


class _ChatForm(Form):
    llm: Annotated[LLMConfig, Field(description="Model")]
    number_of_input_tokens: Annotated[int | None | ModelBoundInputNumber, Field(description="Limit")] = None


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
        AgentClassEntity.objects(agent_class="LLMWrappingAgent").delete()
        yield
        AgentConfigEntityDocument.objects.delete()
        AgentClassEntity.objects(agent_class="LLMWrappingAgent").delete()


def _announce(fill_factor: float | None = 0.85, override_label: LocaleString | None = LocaleString(en="Own")) -> None:
    form = _ChatForm(
        llm=LLMConfig.as_form(include_default_parameter=False),
        number_of_input_tokens=ModelBoundInputNumber(
            label=LocaleString(en="Input tokens"),
            model_ref="llm.model_name",
            max_from="max_input_tokens",
            fill_factor=fill_factor,
            override_label=override_label,
        ),
    )
    AgentClassEntity(
        agent_class="LLMWrappingAgent",
        form=[element.model_dump() for element in form.to_formkit_form()],
        is_conversational=True,
        start_events=[],
        stop_events=[],
        network_graph={},
    ).save(validate=False)  # the event specs a real discovery stores play no part here


@pytest.fixture(autouse=True)
def model_windows():
    def model_info(config: LLMConfig) -> dict[str, Any]:
        if config.model_name not in WINDOWS:
            raise ValueError(f"Model {config.model_name} not found in LiteLLM Proxy.")
        return {"model_info": {"max_input_tokens": WINDOWS[config.model_name]}}

    with patch.object(LLMConfig, "get_model_info", autospec=True, side_effect=model_info):
        yield


def _agent(agent_id: str, model_name: str, **config: Any) -> AgentConfigEntityDocument:
    return AgentConfigEntityDocument(
        agent_class="LLMWrappingAgent",
        agent_id=agent_id,
        name=LocaleStringEntity(en=agent_id),
        description=LocaleStringEntity(en=f"{agent_id} profile"),
        icon="meteor-icons:robot",
        config_data={"llm": {"model_name": model_name}, **config},
    ).save()


def test_a_limit_above_the_window_is_unset(mongo_connection):
    _announce()
    agent = _agent("oversized", SMALL_MODEL, number_of_input_tokens=128000, condense_question=True)

    assert OversizedInputLimitMigration.run() == ["agent LLMWrappingAgent/oversized"]

    config = agent.reload().config_data
    assert config["number_of_input_tokens"] is None
    assert config["condense_question"] is True


def test_a_limit_between_the_bound_and_the_window_is_unset(mongo_connection):
    """It ran at the bound already, and the form would now refuse to save it."""
    _announce()
    agent = _agent("filled", SMALL_MODEL, number_of_input_tokens=65536)

    assert OversizedInputLimitMigration.run() == ["agent LLMWrappingAgent/filled"]
    assert agent.reload().config_data["number_of_input_tokens"] is None


def test_a_limit_within_the_bound_is_kept(mongo_connection):
    """A limit the run can fill may be an admin's cost ceiling."""
    _announce()
    agent = _agent("within", SMALL_MODEL, number_of_input_tokens=BOUND)

    assert OversizedInputLimitMigration.run() == []
    assert agent.reload().config_data["number_of_input_tokens"] == BOUND


def test_a_profile_whose_class_was_never_announced_is_left_alone(mongo_connection):
    agent = _agent("unannounced", SMALL_MODEL, number_of_input_tokens=128000)

    assert OversizedInputLimitMigration.run() == []
    assert agent.reload().config_data["number_of_input_tokens"] == 128000


def test_a_field_without_its_own_unset_state_is_never_unset(mongo_connection):
    """Without an override, None is not 'what the model allows' and could break the profile."""
    _announce(override_label=None)
    agent = _agent("required", SMALL_MODEL, number_of_input_tokens=128000)

    assert OversizedInputLimitMigration.run() == []
    assert agent.reload().config_data["number_of_input_tokens"] == 128000


def test_a_model_without_a_known_window_leaves_the_profile_alone(mongo_connection):
    _announce()
    agent = _agent("unknown", UNKNOWN_MODEL, number_of_input_tokens=128000)

    assert OversizedInputLimitMigration.run() == []
    assert agent.reload().config_data["number_of_input_tokens"] == 128000


def test_a_profile_without_a_limit_is_untouched(mongo_connection):
    _announce()
    _agent("unset", SMALL_MODEL, number_of_input_tokens=None)
    _agent("no_key", SMALL_MODEL)

    assert OversizedInputLimitMigration.run() == []


def test_a_second_run_is_a_no_op(mongo_connection):
    _announce()
    _agent("oversized", SMALL_MODEL, number_of_input_tokens=128000)

    OversizedInputLimitMigration.run()

    assert OversizedInputLimitMigration.run() == []
