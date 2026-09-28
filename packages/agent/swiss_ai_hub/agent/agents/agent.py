import functools
from collections.abc import Callable
from typing import TYPE_CHECKING, ClassVar

from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.events.agent import (
    HumanInTheLoopRequestEvent,
    HumanInTheLoopResponseEvent,
    StartEvent,
    StopEvent,
)
from swiss_ai_hub.core.workflow import DispatchableWorkflow

from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString

if TYPE_CHECKING:
    from swiss_ai_hub.agent.capabilities.capability import Capability


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

    # Capabilities this blueprint installs. Each contributes steps to `get_steps()` next to the ones defined
    # on the class, so the workflow graph, discovery and the meta-question summary all see one flat step set.
    capabilities: ClassVar[tuple[type["Capability"], ...]] = ()

    STEP_ANNOTATION = "_is_agent_step"

    PRECONDITION_FUNCTION_ANNOTATION = "_precondition_fn"
    STOP_ON_ERROR_ANNOTATION = "_stop_on_error"
    MAX_EXECUTION_PER_RUN_ANNOTATION = "_max_executions_per_run"

    @classmethod
    @functools.cache
    def get_own_steps(cls) -> list[Callable]:
        """The steps defined on the class itself, without what its capabilities contribute."""
        return super().get_steps()

    @classmethod
    @functools.cache
    def get_steps(cls) -> list[Callable]:
        steps = list(cls.get_own_steps())
        for capability in cls.capabilities:
            steps.extend(capability.steps_for(cls))
        cls._reject_duplicate_step_names(steps)
        return steps

    @classmethod
    def _reject_duplicate_step_names(cls, steps: list[Callable]) -> None:
        """Step identity is the function name everywhere downstream (step store, tracer, graph), so two
        steps sharing one would silently dedupe each other's executions."""
        seen: set[str] = set()
        for step in steps:
            if step.__name__ in seen:
                raise ValueError(f"{cls.__name__} has two steps named '{step.__name__}'.")
            seen.add(step.__name__)

    @classmethod
    def validate_capabilities(cls, agent_config_type: type[AgentConfig]) -> None:
        """Fail at runner start when a capability's steps would ask the dispatcher for a form mixin the
        blueprint's config does not list as a base."""
        for capability in cls.capabilities:
            if not issubclass(agent_config_type, capability.required_config):
                raise TypeError(
                    f"{cls.__name__} installs {capability.__name__}, which needs a config with the "
                    f"{capability.required_config.__name__} mixin, but {agent_config_type.__name__} lacks it."
                )

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
        return {event for event in output_events if issubclass(event, StopEvent)}

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
