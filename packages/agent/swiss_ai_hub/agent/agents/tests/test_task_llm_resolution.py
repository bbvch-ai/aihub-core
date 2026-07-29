"""Cross-agent coverage for the optional `task_llm` model used by auxiliary/classification steps."""

from collections.abc import Callable
from typing import Any

import pytest
from swiss_ai_hub.core.agents import AgentConfig, AgentRef
from swiss_ai_hub.core.form import ALL_FORM_OPTIONS, ModelSelect  # noqa: F401 — triggers Group/Repeater rebuild
from swiss_ai_hub.core.generative_ai import LLMConfig, LLMParameter
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.mcp import McpClientConfig

from swiss_ai_hub.agent.agents.expert_asking_agent.expert_asking_agent_config import (
    ChannelConfig,
    ExpertAskingAgentConfig,
)
from swiss_ai_hub.agent.agents.expert_rag_agent.configs.expert_rag_agent_config import ExpertRAGAgentConfig
from swiss_ai_hub.agent.agents.few_shot_agent.few_shot_agent_config import FewShotAgentConfig
from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent_config import LLMWrappingAgentConfig
from swiss_ai_hub.agent.agents.mcp_react_agent.configs.mcp_react_agent_config import McpReactAgentConfig
from swiss_ai_hub.agent.agents.namespace_selection_agent.configs.namespace_selection_agent_config import (
    NamespaceSelectionAgentConfig,
)
from swiss_ai_hub.agent.agents.namespace_selection_agent.configs.rag_delegation_config import RAGDelegationConfig
from swiss_ai_hub.agent.agents.rag_agent.configs.expert_escalation_config import ExpertEscalationConfig
from swiss_ai_hub.agent.agents.rag_agent.configs.rag_agent_config import RAGAgentConfig
from swiss_ai_hub.agent.steps.prompting.few_shot_step.few_shot_step_config import FewShotStepConfig

MAIN_MODEL = "text-generation/main-model"
TASK_MODEL = "text-generation/task-model"


def _identity(**overrides: Any) -> dict[str, Any]:
    return {
        "agent_id": "test-agent",
        "name": LocaleString(en="Test Agent"),
        "description": LocaleString(en="Agent used to verify task_llm resolution."),
        "llm": LLMConfig(model_name=MAIN_MODEL),
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


def _namespace_config(**overrides: Any) -> NamespaceSelectionAgentConfig:
    return NamespaceSelectionAgentConfig(
        **_identity(
            bucket_names=["knowledge"],
            rag_delegation=RAGDelegationConfig(rag_agent=AgentRef(agent_class="RAGAgent", agent_id="rag")),
            **overrides,
        )
    )


def _few_shot_config(**overrides: Any) -> FewShotAgentConfig:
    return FewShotAgentConfig(
        **_identity(
            few_shot=FewShotStepConfig(system_prompt=LocaleString(en="Follow the examples.")),
            **overrides,
        )
    )


def _llm_wrapping_config(**overrides: Any) -> LLMWrappingAgentConfig:
    return LLMWrappingAgentConfig(
        **_identity(
            system_prompt=LocaleString(en="You are helpful."),
            **overrides,
        )
    )


def _expert_asking_config(**overrides: Any) -> ExpertAskingAgentConfig:
    return ExpertAskingAgentConfig(
        **_identity(
            channel_config=ChannelConfig(),
            **overrides,
        )
    )


def _mcp_react_config(**overrides: Any) -> McpReactAgentConfig:
    return McpReactAgentConfig(
        **_identity(
            mcp=McpClientConfig(name="test", url="http://localhost:8000/mcp", timeout=30.0),
            max_iterations=10,
            number_of_input_tokens=128000,
            **overrides,
        )
    )


CONFIG_FACTORIES: list[Callable[..., AgentConfig]] = [
    _rag_config,
    _expert_rag_config,
    _namespace_config,
    _few_shot_config,
    _llm_wrapping_config,
    _expert_asking_config,
    _mcp_react_config,
]


@pytest.mark.parametrize("build_config", CONFIG_FACTORIES, ids=lambda f: f.__name__)
def test_unset_task_llm_defaults_to_the_main_llm(build_config: Callable[..., AgentConfig]) -> None:
    config = build_config()

    assert config.task_llm.model_name == config.llm.model_name


@pytest.mark.parametrize("build_config", CONFIG_FACTORIES, ids=lambda f: f.__name__)
def test_task_llm_is_not_aliased_to_the_main_llm(build_config: Callable[..., AgentConfig]) -> None:
    """Sharing the instance would make a write to one config silently mutate the other."""
    config = build_config()

    assert config.task_llm is not config.llm
    config.task_llm.default_parameter.temperature = 1.5
    assert config.llm.default_parameter.temperature == 0.0


@pytest.mark.parametrize("build_config", CONFIG_FACTORIES, ids=lambda f: f.__name__)
def test_task_llm_is_used_when_configured(build_config: Callable[..., AgentConfig]) -> None:
    config = build_config(task_llm=LLMConfig(model_name=TASK_MODEL))

    assert config.task_llm.model_name == TASK_MODEL


@pytest.mark.parametrize("build_config", CONFIG_FACTORIES, ids=lambda f: f.__name__)
def test_task_llm_inherits_generation_parameters_from_the_main_llm(
    build_config: Callable[..., AgentConfig],
) -> None:
    """The form only picks a model, so parameters must mirror the main llm with log probabilities off."""
    config = build_config(
        llm=LLMConfig(
            model_name=MAIN_MODEL,
            default_parameter=LLMParameter(temperature=0.7, timeout=42.0, logprobs=True, top_logprobs=5),
        ),
        task_llm=LLMConfig(model_name=TASK_MODEL, default_parameter=LLMParameter(temperature=1.9, timeout=1.0)),
    )

    assert config.task_llm.default_parameter.temperature == 0.7
    assert config.task_llm.default_parameter.timeout == 42.0
    assert config.task_llm.default_parameter.logprobs is False
    assert config.task_llm.default_parameter.top_logprobs == 0


@pytest.mark.parametrize("build_config", CONFIG_FACTORIES, ids=lambda f: f.__name__)
def test_blank_task_llm_model_falls_back_to_main_llm(build_config: Callable[..., AgentConfig]) -> None:
    """A blank picker submission must not route auxiliary steps to an empty model."""
    config = build_config(task_llm=LLMConfig(model_name=""))

    assert config.task_llm.model_name == config.llm.model_name


@pytest.mark.parametrize("build_config", CONFIG_FACTORIES, ids=lambda f: f.__name__)
def test_task_llm_survives_model_validate_round_trip(build_config: Callable[..., AgentConfig]) -> None:
    """The dispatcher reconstructs configs via model_validate — resolution must hold there too."""
    config = build_config(task_llm=LLMConfig(model_name=TASK_MODEL))
    reconstructed = type(config).model_validate(config.model_dump())

    assert reconstructed.task_llm.model_name == TASK_MODEL


CONFIG_TYPES: list[type[AgentConfig]] = [
    RAGAgentConfig,
    ExpertRAGAgentConfig,
    NamespaceSelectionAgentConfig,
    FewShotAgentConfig,
    LLMWrappingAgentConfig,
    ExpertAskingAgentConfig,
    McpReactAgentConfig,
]


@pytest.mark.parametrize("config_type", CONFIG_TYPES, ids=lambda t: t.__name__)
def test_form_mode_keeps_the_task_llm_picker(config_type: type[AgentConfig]) -> None:
    """The defaulting validator must not overwrite the form-mode picker with the main llm's picker."""
    form = config_type.as_form()

    assert isinstance(form.task_llm.model_name, ModelSelect)
    assert form.task_llm is not form.llm


@pytest.mark.parametrize("config_type", CONFIG_TYPES, ids=lambda t: t.__name__)
def test_task_llm_renders_a_model_picker_and_is_optional_at_submission(config_type: type[AgentConfig]) -> None:
    form = config_type.as_form()

    task_llm_group = next(element for element in form.to_formkit_form() if element.name == "task_llm")
    assert any(child.name == "model_name" for child in task_llm_group.children)

    submission_field = form.to_configurable_submission_model().model_fields["task_llm"]
    assert not submission_field.is_required()


@pytest.mark.parametrize("config_type", CONFIG_TYPES, ids=lambda t: t.__name__)
def test_task_llm_form_omits_the_parameter_group(config_type: type[AgentConfig]) -> None:
    """Task-model parameters are derived from the main llm, so they must not be offered as inputs."""
    elements = config_type.as_form().to_formkit_form()

    task_llm_group = next(element for element in elements if element.name == "task_llm")
    assert [child.name for child in task_llm_group.children] == ["model_name"]

    llm_group = next(element for element in elements if element.name == "llm")
    assert any(child.name == "default_parameter" for child in llm_group.children)


@pytest.mark.parametrize("config_type", CONFIG_TYPES, ids=lambda t: t.__name__)
def test_task_llm_group_explains_which_steps_use_it(config_type: type[AgentConfig]) -> None:
    """The enable toggle carries the help text, so admins learn what the task model is used for."""
    form = config_type.as_form()

    task_llm_group = next(element for element in form.to_formkit_form() if element.name == "task_llm")
    assert task_llm_group.nullable
    assert task_llm_group.label == "Task LLM"
    assert task_llm_group.help == config_type.model_fields["task_llm"].description
    assert task_llm_group.help != task_llm_group.label
