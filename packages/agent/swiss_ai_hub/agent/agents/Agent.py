import functools
from typing import ClassVar

from swiss_ai_hub.core.nats.events import HumanInTheLoopRequestEvent, HumanInTheLoopResponseEvent
from swiss_ai_hub.core.nats.events.control.start import StartEvent
from swiss_ai_hub.core.nats.events.control.stop import StopEvent
from swiss_ai_hub.core.nats.workflow.DispatchableWorkflow import DispatchableWorkflow

from swiss_ai_hub.agent.i18n.AgentLocaleString import AgentLocaleString


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

    STEP_ANNOTATION = "_is_agent_step"

    PRECONDITION_FUNCTION_ANNOTATION = "_precondition_fn"
    STOP_ON_ERROR_ANNOTATION = "_stop_on_error"
    MAX_EXECUTION_PER_RUN_ANNOTATION = "_max_executions_per_run"

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
