import functools
from typing import ClassVar

from swiss_ai_hub.core.nats.events import (
    AgentWorkEvent,
    AgentWorkRequestEvent,
    HumanWorkEvent,
    HumanWorkRequestEvent,
    ProgramWorkEvent,
    ProgramWorkRequestEvent,
    WorkEvent,
    WorkRequestEvent,
)
from swiss_ai_hub.core.nats.events.work.process.ProcessWorkEvent import ProcessWorkEvent
from swiss_ai_hub.core.nats.workflow.DispatchableWorkflow import DispatchableWorkflow

from swiss_ai_hub.process.delegators.AbstractProcessEntity import BaseProcessEntity
from swiss_ai_hub.process.delegators.agent.Agent import Agent
from swiss_ai_hub.process.delegators.human.Human import Human
from swiss_ai_hub.process.delegators.process.Process import Process
from swiss_ai_hub.process.delegators.program.Program import Program
from swiss_ai_hub.process.i18n.ProcessLocaleString import ProcessLocaleString


class AgenticProcess(DispatchableWorkflow):
    """
    The agentic process is a dispatchable workflow that connects agents, humans and programs to form a
    well-defined process.

    In an agentic process, the steps you define describe 'connections' with 'transformations' between
    different entities. Your main goal is simple:
    - Define what the inputs and outputs of your process are.
    - Divide your process into a series of work that must be done
    - Decide for each work what entity should do the work: An agent, a human or a program.
    - Delegate the work to the right entity
    - Wait for the delegated work to be completed, take the result, transform it, and delegate to the next entity.
    - Hence, through a series of work delegations, the process input (start)
      is transformed into the process output (end).

    The process itself should never do work on its own. As soon as you start implementing logic within a process step,
    you are off-track. Everything you do within a process step should be delegated to an entity, and the
    process should at most transform the outputs of one (or more) entities to be a valid input for the next entity.

    To define class-level metadata, override these class variables in your subclass:
    - name: Display name for the process class (LocaleString)
    - description: Description of the process's purpose (LocaleString)
    - icon: Icon identifier for the process (str)
    """

    name: ClassVar[ProcessLocaleString] = ProcessLocaleString.from_i18n_path("process.processes.base.name")
    description: ClassVar[ProcessLocaleString] = ProcessLocaleString.from_i18n_path(
        "process.processes.base.description"
    )
    icon: ClassVar[str] = "mage:broadcast"

    STEP_ANNOTATION = "_is_process_step"

    PROCESS_INPUTS_ANNOTATION = "_process_inputs"
    PROCESS_OUTPUTS_ANNOTATION = "_process_outputs"

    @classmethod
    @functools.cache
    def get_events_with_in_type(
        cls, config_class: type[BaseProcessEntity.In]
    ) -> list[tuple[type[WorkEvent], BaseProcessEntity.In]]:
        """
        Scans all process steps to find inputs matching a specific configuration class.
        This now iterates over the pre-processed list stored on each step method.
        """
        found_events = []
        for step_method in cls.get_steps():
            # Iterate through the list of (event, config) tuples stored by the decorator
            for event_type, config_instance in getattr(step_method, cls.PROCESS_INPUTS_ANNOTATION, []):
                if isinstance(config_instance, config_class):
                    found_events.append((event_type, config_instance))
        return found_events

    @classmethod
    @functools.cache
    def get_events_with_agent_in(cls) -> list[tuple[type[AgentWorkEvent], Agent.In]]:
        return cls.get_events_with_in_type(Agent.In)

    @classmethod
    @functools.cache
    def get_events_with_human_in(cls) -> list[tuple[type[HumanWorkEvent], Human.In]]:
        return cls.get_events_with_in_type(Human.In)

    @classmethod
    @functools.cache
    def get_events_with_program_in(cls) -> list[tuple[type[ProgramWorkEvent], Program.In]]:
        return cls.get_events_with_in_type(Program.In)

    @classmethod
    @functools.cache
    def get_events_with_process_in(cls) -> list[tuple[type[ProcessWorkEvent], Process.In]]:
        return cls.get_events_with_in_type(Process.In)

    @classmethod
    @functools.cache
    def get_events_with_out_type(
        cls, config_class: type[BaseProcessEntity.Out]
    ) -> list[tuple[type[WorkRequestEvent], BaseProcessEntity.Out]]:
        """
        Scans all process steps to find outputs matching a specific configuration class.
        This now iterates over the pre-processed list stored on each step method.
        """
        found_events = []
        for step_method in cls.get_steps():
            # Iterate through the list of (event, config) tuples stored by the decorator
            for event_type, config_instance in getattr(step_method, "_process_outputs", []):
                if isinstance(config_instance, config_class):
                    found_events.append((event_type, config_instance))
        return found_events

    @classmethod
    @functools.cache
    def get_events_with_agent_out(cls) -> list[tuple[type[AgentWorkRequestEvent], Agent.Out]]:
        return cls.get_events_with_out_type(Agent.Out)

    @classmethod
    @functools.cache
    def get_events_with_human_out(cls) -> list[tuple[type[HumanWorkRequestEvent], Human.Out]]:
        return cls.get_events_with_out_type(Human.Out)

    @classmethod
    @functools.cache
    def get_events_with_program_out(cls) -> list[tuple[type[ProgramWorkRequestEvent], Program.Out]]:
        return cls.get_events_with_out_type(Program.Out)
