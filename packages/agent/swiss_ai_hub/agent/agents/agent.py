import functools
from collections.abc import Callable
from typing import TYPE_CHECKING, ClassVar

from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.events.agent import (
    ChatFeature,
    HumanInTheLoopRequestEvent,
    HumanInTheLoopResponseEvent,
    StartEvent,
    StopEvent,
)
from swiss_ai_hub.core.workflow import DispatchableWorkflow

from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString

if TYPE_CHECKING:
    from swiss_ai_hub.agent.capabilities.capability import Capability
    from swiss_ai_hub.agent.capabilities.tool_loop.tool_set import ToolSet


class Agent(DispatchableWorkflow):
    """
    An agent is a dispatchable workflow that tries to get some work done by defining a series of
    operations that is performed on the input data to achieve a pre-defined goal - the agents output.

    In an agentic workflow, steps define a series of 'operations' that need to be performed in order
    to bring the agents input (StartEvent) one step closer to the desired output (StopEvent).

    You main goal is simple:
    - Define the input and output of your agent: What data should it receive, what should it return
    - Divide your agentic workflow into a series of steps that must be executed to achieve the goal.
    - For each step, decide what outputs from previous steps it requires and what it produces.
    - Hence, through a series of operations, the agent input (start) it processed to achieve the agent output (stop).

    Your agent should always do one thing and do it well. It should emit in-between results to the user
    through display events, but it should also always define a clear final output in the form of a
    StopEvent (or a subclass of it) that defines all relevant attributes.

    Many agents can be used in three different settings, which you must keep in mind while designing your agent:
    - As an assistant, in which case some user sends a message to the agent and the agent responds.
    - As an agent within an agentic process, in which the agent performs one piece of work as part of a process.
    - As an agent that is called from another agent to deliver a result which the other agent can use to
      fulfil ITS goal.

    Usually, marking the agent as an assistant is as simply as accepting the UserMessageEvent as a StartEvent,
    as it makes the agent 'conversational'. However, try not to limit your agents to conversations only, as it
    makes the agent inflexible to participate in other types of interactions.

    To define class-level metadata, override these class variables in your subclass:
    - name: Display name for the agent class (LocaleString)
    - description: Description of the agent's purpose (LocaleString)
    - icon: Icon identifier for the agent (str)
    """

    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path("agent.base_agent.metadata.name")
    description: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path("agent.base_agent.metadata.description")
    icon: ClassVar[str] = "mage:robot"

    # Whether the runner answers class-discovery requests. Set False for internal/system agents (e.g. the
    # memory-writer) that are triggered programmatically and must NOT appear as a user-facing blueprint in the
    # Admin UI. Non-discoverable agents still subscribe to and process their control events normally.
    discoverable: ClassVar[bool] = True

    # The stop events a blueprint ends its runs with by handing them to `Conversation.complete(stop=...)`. They
    # travel inside the request's payload, so no step's return type names them; without this declaration the
    # REST response model and the workflow graph fall back to the bare `StopEvent` and drop their fields.
    completion_stops: ClassVar[tuple[type[StopEvent], ...]] = ()

    STEP_ANNOTATION = "_is_agent_step"

    PRECONDITION_FUNCTION_ANNOTATION = "_precondition_fn"
    STOP_ON_ERROR_ANNOTATION = "_stop_on_error"
    MAX_EXECUTION_PER_RUN_ANNOTATION = "_max_executions_per_run"

    @classmethod
    @functools.cache
    def get_own_steps(cls) -> list[Callable]:
        """The steps defined on the class itself, without the capabilities its calls pull in."""
        return super().get_steps()

    @classmethod
    @functools.cache
    def installed_capabilities(cls) -> list["type[Capability]"]:
        """Derived, never declared: returning a capability's request event from a step is what installs it."""
        from swiss_ai_hub.agent.capabilities.catalog import CapabilityCatalog

        return CapabilityCatalog.called_by(cls.get_own_steps(), cls.declared_tool_capabilities())

    @classmethod
    @functools.cache
    def get_steps(cls) -> list[Callable]:
        """The blueprint's own steps plus the capability steps its calls can trigger, as one flat set."""
        from swiss_ai_hub.agent.capabilities.catalog import CapabilityCatalog

        return [
            *cls.get_own_steps(),
            *CapabilityCatalog.reachable_steps(cls.get_own_steps(), cls.declared_tool_capabilities()),
        ]

    @classmethod
    @functools.cache
    def tool_sets(cls) -> list["ToolSet"]:
        """The tool sets the blueprint declares as class attributes with `ToolLoop.over(...)`, inherited ones too."""
        from swiss_ai_hub.agent.capabilities.tool_loop.tool_set import ToolSet

        found: dict[str, ToolSet] = {}
        for klass in reversed(cls.__mro__):
            found |= {name: value for name, value in vars(klass).items() if isinstance(value, ToolSet)}
        return list(found.values())

    @classmethod
    def tool_set(cls, name: str) -> "ToolSet":
        return next(tool_set for tool_set in cls.tool_sets() if tool_set.name == name)

    @classmethod
    def tool_set_offering(cls, tool_name: str | None) -> "ToolSet | None":
        return next((tool_set for tool_set in cls.tool_sets() if tool_name in tool_set.names()), None)

    @classmethod
    def declared_tool_capabilities(cls) -> list["type[Capability]"]:
        """Declaring a capability as a tool installs it, so a model-chosen call can run its steps."""
        return list(dict.fromkeys(c for tool_set in cls.tool_sets() for c in tool_set.capabilities))

    @classmethod
    def validate_workflow(cls, agent_config_type: type[AgentConfig]) -> None:
        """Refuse a blueprint whose composed workflow would stall or crash before it runs.

        Called by the runner with the config it was handed. Collects every problem at once: a step waiting for
        an event nothing produces, two steps sharing a name, and a capability whose form mixin the config lacks.
        """
        from swiss_ai_hub.agent.workflow.workflow_validation import WorkflowValidation

        WorkflowValidation.for_blueprint(cls, agent_config_type).raise_for_problems()

    @classmethod
    def supported_features(cls) -> set[ChatFeature]:
        """Derived, never declared: calling the capability that serves a feature is what makes it supported."""
        return {
            capability.chat_feature
            for capability in cls.installed_capabilities()
            if capability.chat_feature is not None
        } | {feature for tool_set in cls.tool_sets() for feature in tool_set.chat_features()}

    @classmethod
    @functools.cache
    def get_start_events(cls) -> set[type[StartEvent]]:
        """
        Returns all event types that are considered start events (subclasses of StartEvent).
        These events indicate how a run/workflow can be initiated.
        """
        input_events = cls.get_input_events()
        return {event for event in input_events if issubclass(event, StartEvent)}

    @classmethod
    @functools.cache
    def get_stop_events(cls) -> set[type[StopEvent]]:
        """
        Returns all event types that are considered stop events (subclasses of StopEvent).
        These events indicate how a run/workflow can terminate.
        """
        output_events = cls.get_output_events()
        return {event for event in output_events if issubclass(event, StopEvent)} | set(cls.completion_stops)

    @classmethod
    @functools.cache
    def get_hitl_request_events(cls) -> set[type]:
        """
        Returns all event types that are human-in-the-loop request events.
        These events indicate when the agent requests human intervention.
        """
        output_events = cls.get_output_events()
        return {event for event in output_events if issubclass(event, HumanInTheLoopRequestEvent)}

    @classmethod
    @functools.cache
    def get_hitl_response_events(cls) -> set[type]:
        """
        Returns all event types that are human-in-the-loop response events.
        These events indicate how humans can respond to HITL requests.
        """
        input_events = cls.get_input_events()
        return {event for event in input_events if issubclass(event, HumanInTheLoopResponseEvent)}
