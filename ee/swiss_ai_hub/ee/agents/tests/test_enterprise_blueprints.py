"""The enterprise blueprints keep the rules every open blueprint is held to; the open package's own checks walk only
its own agents, so these repeat them for the two that left it."""

import inspect

import pytest

# rag_agent first: rag.preconditions/step_functions only import cleanly in the runtime (rag_agent-first) order.
import swiss_ai_hub.agent.agents.rag_agent  # noqa: F401
from swiss_ai_hub.agent import Agent, AgentRunner
from swiss_ai_hub.core.agents import ANONYMISE_CONFIG_KEY, CRON_CONFIG_KEY, AgentConfig
from swiss_ai_hub.core.events.agent import ChatFeature
from swiss_ai_hub.core.form import ConfigSpecs
from swiss_ai_hub.core.form.elements.checkbox import Checkbox

from swiss_ai_hub.ee.agents.email_classification_agent.configs.email_classification_agent_config import (
    EmailClassificationAgentConfig,
)
from swiss_ai_hub.ee.agents.email_classification_agent.email_classification_agent import EmailClassificationAgent
from swiss_ai_hub.ee.agents.universal_agent.universal_agent import UniversalAgent
from swiss_ai_hub.ee.agents.universal_agent.universal_agent_config import UniversalAgentConfig

BLUEPRINTS: list[tuple[type[Agent], type[AgentConfig]]] = [
    (EmailClassificationAgent, EmailClassificationAgentConfig),
    (UniversalAgent, UniversalAgentConfig),
]
AGENTS = [agent for agent, _ in BLUEPRINTS]
# The tool loop joins its own iterations outside the step inputs, so only fixed-flow blueprints are held to this.
FIXED_FLOW_AGENTS = [EmailClassificationAgent]


def _steps_with_preconditions(agent: type[Agent]):
    for step_method in agent.get_steps():
        precondition_fn = getattr(step_method, Agent.PRECONDITION_FUNCTION_ANNOTATION, None)
        if precondition_fn is not None:
            yield step_method, precondition_fn


@pytest.mark.parametrize("blueprint", AGENTS, ids=lambda blueprint: blueprint.__name__)
def test_an_agent_class_defines_only_steps(blueprint: type[Agent]) -> None:
    helpers = [
        name
        for name, member in vars(blueprint).items()
        if inspect.isfunction(inspect.unwrap(getattr(member, "__func__", member)))
        and not getattr(getattr(member, "__func__", member), Agent.STEP_ANNOTATION, False)
    ]

    assert not helpers, f"{blueprint.__name__} defines helpers {helpers}; move them into a class its steps import"


@pytest.mark.parametrize("agent", FIXED_FLOW_AGENTS, ids=lambda agent: agent.__name__)
def test_no_precondition_asks_for_an_event_its_step_does_not_declare(agent: type[Agent]) -> None:
    for step_method, precondition_fn in _steps_with_preconditions(agent):
        step_events = getattr(step_method, Agent.INPUT_EVENTS_ANNOTATION, set())
        precondition_events = getattr(precondition_fn, Agent.INPUT_EVENTS_ANNOTATION, set())

        assert not precondition_events - step_events, f"{agent.__name__}.{step_method.__name__}"


@pytest.mark.parametrize("agent", FIXED_FLOW_AGENTS, ids=lambda agent: agent.__name__)
def test_every_required_precondition_parameter_can_actually_be_filled(agent: type[Agent]) -> None:
    for step_method, precondition_fn in _steps_with_preconditions(agent):
        step_events = getattr(step_method, Agent.INPUT_EVENTS_ANNOTATION, set())
        mapping = getattr(precondition_fn, Agent.INPUT_EVENT_MAPPING_ANNOTATION, {})

        for name, parameter in inspect.signature(precondition_fn).parameters.items():
            if parameter.default is not inspect.Parameter.empty or name not in mapping:
                continue
            assert mapping[name] & step_events, f"{agent.__name__}.{step_method.__name__}: {name}"


@pytest.mark.parametrize(("agent", "config"), BLUEPRINTS, ids=lambda value: value.__name__)
def test_should_offer_the_anonymisation_toggle(agent: type[Agent], config: type[AgentConfig]) -> None:
    runner = AgentRunner(agent_type=agent, agent_config=config.as_form())

    names = [element.name for element in runner._published_form()]
    platform = [name for name in names if name in (ANONYMISE_CONFIG_KEY, CRON_CONFIG_KEY)]

    assert isinstance(runner.published_config.anonymise, Checkbox)
    assert names[-len(platform) :] == platform
    assert platform[0] == ANONYMISE_CONFIG_KEY
    specs = ConfigSpecs.from_form(runner.published_config, runner.agent_class)
    assert specs.config_schema["properties"][ANONYMISE_CONFIG_KEY]["type"] == "boolean"


def test_the_mailbox_secrets_are_read_off_the_email_config_form() -> None:
    assert EmailClassificationAgentConfig.secret_field_paths() == {"imap.password", "imap.client_secret"}


def test_the_universal_agent_supports_a_response_schema() -> None:
    assert UniversalAgent.supports_response_schema()


def test_the_universal_agent_offers_the_code_interpreter_and_my_files_toggles() -> None:
    assert {ChatFeature.CODE_INTERPRETER, ChatFeature.USER_FILES} <= UniversalAgent.supported_features()
