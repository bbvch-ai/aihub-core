"""The MCP ReAct agent drives its loop through tool calls, so its answering model must support them; the task model
only classifies and titles, so its picker stays unrestricted."""

from swiss_ai_hub.core.events import BaseEvent
from swiss_ai_hub.core.events.agent import AgentClassDiscoveryResponseEvent
from swiss_ai_hub.core.form import (
    ALL_FORM_OPTIONS,  # noqa: F401 — rebuilds Group/Repeater
    ConfigSpecs,
    ModelSelect,
)
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import ModelCapability, ModelRequirements
from swiss_ai_hub.core.workflow import WorkflowVisualizer

from swiss_ai_hub.agent.agents.mcp_react_agent import McpReactAgent, McpReactAgentConfig


def _picker(group_name: str) -> ModelSelect:
    group = next(element for element in McpReactAgentConfig.as_form().to_formkit_form() if element.name == group_name)
    return next(child for child in group.children if isinstance(child, ModelSelect))


def test_the_answering_model_must_support_tool_calling():
    assert _picker("llm").requirements == ModelRequirements(capabilities={ModelCapability.TOOL_CALLING})


def test_the_task_model_has_no_requirements():
    assert _picker("task_llm").requirements == ModelRequirements()


def test_the_requirements_survive_the_discovery_event_the_api_parses():
    """The form reaches the API inside a NATS event, serialised with `serialize_as_any`; a requirement that does not
    come back as a set of capabilities makes the API reject the agent's whole announcement on every round."""
    announcement = AgentClassDiscoveryResponseEvent(
        agent_class="McpReactAgent",
        name=LocaleString(en="MCP ReAct"),
        description=LocaleString(en="MCP ReAct"),
        form=McpReactAgentConfig.as_form().to_formkit_form(),
        agent_config_specs=ConfigSpecs.from_form(McpReactAgentConfig.as_form(), "McpReactAgent"),
        is_conversational=True,
        start_events=[],
        stop_events=[],
        hitl_request_events=[],
        hitl_response_events=[],
        network_graph=WorkflowVisualizer(agent=McpReactAgent).build(),
    )

    received = BaseEvent.deserialize_event(announcement.model_dump_json())

    pickers = {
        group.name: next(child for child in group.children if isinstance(child, ModelSelect))
        for group in received.form
        if group.name in ("llm", "task_llm")
    }
    assert pickers["llm"].requirements.capabilities == {ModelCapability.TOOL_CALLING}
    assert pickers["task_llm"].requirements == ModelRequirements()
