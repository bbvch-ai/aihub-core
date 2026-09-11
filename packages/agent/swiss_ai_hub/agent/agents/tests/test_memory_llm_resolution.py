"""Coverage for the optional per-agent memory model used by memory extraction (issue #1590).

The fallback is a deployment setting (`MEM0_LLM_NAME`), not a sibling field, so nothing resolves it on the
config: an unconfigured profile reports `None` and `AgentMemory` supplies the platform default. What is
asserted here is that the platform's hook reads the blueprint's picker, and that the three shapes meaning
"no choice" — unset, blank, and a form-mode element — all reduce to `None`.
"""

from typing import Any

import pytest
from swiss_ai_hub.core.agents import AgentConfig, AgentRef
from swiss_ai_hub.core.form import ALL_FORM_OPTIONS, ModelSelect  # noqa: F401 — triggers Group/Repeater rebuild
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.expert_asking_agent.expert_asking_agent_config import (
    ChannelConfig,
    ExpertAskingAgentConfig,
)
from swiss_ai_hub.agent.agents.expert_rag_agent.configs.expert_rag_agent_config import ExpertRAGAgentConfig
from swiss_ai_hub.agent.agents.rag_agent.configs.expert_escalation_config import ExpertEscalationConfig
from swiss_ai_hub.agent.agents.rag_agent.configs.rag_agent_config import RAGAgentConfig
from swiss_ai_hub.agent.agents.rag_agent.configs.user_memory_config import UserMemoryConfig

MEMORY_MODEL = "text-generation/memory-model"


def _identity(**overrides: Any) -> dict[str, Any]:
    return {
        "agent_id": "test-agent",
        "name": LocaleString(en="Test Agent"),
        "description": LocaleString(en="Agent used to verify memory_llm resolution."),
        "llm": LLMConfig(model_name="text-generation/main-model"),
        **overrides,
    }


def _rag_config(**overrides: Any) -> RAGAgentConfig:
    return RAGAgentConfig(**_identity(retrievers=[], **overrides))


def _expert_rag_config(**overrides: Any) -> ExpertRAGAgentConfig:
    return ExpertRAGAgentConfig(
        **_identity(
            retrievers=[],
            expert_escalation=ExpertEscalationConfig(
                agent=AgentRef(agent_class="ExpertAskingAgent", agent_id="expert")
            ),
            **overrides,
        )
    )


CONFIG_FACTORIES = [_rag_config, _expert_rag_config]
CONFIG_TYPES: list[type[AgentConfig]] = [RAGAgentConfig, ExpertRAGAgentConfig]


@pytest.mark.parametrize("build_config", CONFIG_FACTORIES, ids=lambda f: f.__name__)
def test_unset_memory_llm_resolves_to_none(build_config) -> None:
    """Existing profiles carry no memory model and must keep using the platform default."""
    assert build_config().memory_llm_model_name is None


@pytest.mark.parametrize("build_config", CONFIG_FACTORIES, ids=lambda f: f.__name__)
def test_configured_memory_llm_is_reported(build_config) -> None:
    config = build_config(user_memory=UserMemoryConfig(memory_llm=MEMORY_MODEL))

    assert config.memory_llm_model_name == MEMORY_MODEL


@pytest.mark.parametrize("build_config", CONFIG_FACTORIES, ids=lambda f: f.__name__)
def test_blank_memory_llm_resolves_to_none(build_config) -> None:
    """A blank picker submission must not route extraction to an empty model name."""
    config = build_config(user_memory=UserMemoryConfig(memory_llm=""))

    assert config.memory_llm_model_name is None


@pytest.mark.parametrize("build_config", CONFIG_FACTORIES, ids=lambda f: f.__name__)
def test_memory_llm_survives_model_validate_round_trip(build_config) -> None:
    """The dispatcher reconstructs configs via model_validate — the hook must hold there too."""
    config = build_config(user_memory=UserMemoryConfig(memory_llm=MEMORY_MODEL))
    reconstructed = type(config).model_validate(config.model_dump())

    assert reconstructed.memory_llm_model_name == MEMORY_MODEL


def test_a_blueprint_without_a_memory_model_reports_none() -> None:
    """The dispatcher injects AgentMemory for every blueprint, so the base hook must answer for all of them."""
    config = AgentConfig(
        agent_id="plain", name=LocaleString(en="Plain"), description=LocaleString(en="No memory picker")
    )

    assert config.memory_llm_model_name is None


def test_expert_asking_agent_has_no_memory_model() -> None:
    """It writes organization memory verbatim (infer=False), so no extraction model applies."""
    config = ExpertAskingAgentConfig(**_identity(channel_config=ChannelConfig()))

    assert config.memory_llm_model_name is None


@pytest.mark.parametrize("config_type", CONFIG_TYPES, ids=lambda t: t.__name__)
def test_form_mode_reports_no_model(config_type: type[AgentConfig]) -> None:
    """In form mode the value is a picker element, which is not a model name."""
    assert config_type.as_form().memory_llm_model_name is None


@pytest.mark.parametrize("config_type", CONFIG_TYPES, ids=lambda t: t.__name__)
def test_form_renders_a_model_picker_gated_on_storage(config_type: type[AgentConfig]) -> None:
    """Choosing an extraction model is meaningless while storage is off, so the picker follows that toggle."""
    form = config_type.as_form()

    user_memory_group = next(element for element in form.to_formkit_form() if element.name == "user_memory")
    picker = next(child for child in user_memory_group.children if child.name == "memory_llm")

    assert picker.formkit == "modelSelect"
    assert picker.mode == "chat"
    assert picker.condition_if == "$get(check_user_memory_storage_enabled).value"


@pytest.mark.parametrize("config_type", CONFIG_TYPES, ids=lambda t: t.__name__)
def test_the_picker_offers_an_unset_state(config_type: type[AgentConfig]) -> None:
    """Nullability is what renders the enable toggle — without it an admin could never go back to the default."""
    form = config_type.as_form()

    user_memory_group = next(element for element in form.to_formkit_form() if element.name == "user_memory")
    picker = next(child for child in user_memory_group.children if child.name == "memory_llm")

    assert picker.nullable is True
    assert picker.default_enabled is False
    assert picker.required is False


@pytest.mark.parametrize("config_type", CONFIG_TYPES, ids=lambda t: t.__name__)
def test_memory_llm_is_optional_at_submission(config_type: type[AgentConfig]) -> None:
    """Profiles saved before the field existed omit it entirely and must still validate."""
    submission_model = config_type.as_form().to_configurable_submission_model()
    user_memory_field = submission_model.model_fields["user_memory"]

    assert not user_memory_field.annotation.model_fields["memory_llm"].is_required()
