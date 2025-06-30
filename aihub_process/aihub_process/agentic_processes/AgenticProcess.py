import functools
from typing import List, Tuple, Type

from aihub_lib.nats.events import (
    AgentWorkEvent,
    AgentWorkRequestEvent,
    HumanWorkEvent,
    HumanWorkRequestEvent,
    ProgramWorkEvent,
    ProgramWorkRequestEvent,
    WorkEvent,
    WorkRequestEvent,
)
from aihub_lib.nats.events.work.process.ProcessWorkEvent import ProcessWorkEvent
from aihub_lib.nats.workflow.DispatchableWorkflow import DispatchableWorkflow

from aihub_process.delegators.AbstractProcessEntity import BaseProcessEntity
from aihub_process.delegators.agent.Agent import Agent
from aihub_process.delegators.human.Human import Human
from aihub_process.delegators.process.Process import Process
from aihub_process.delegators.program.Program import Program


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
    - Hence, through a series of work delegations, the process input (start) is transformed into the process output (end).

    The process itself should never do work on its own. As soon as you start implementing logic within a process step,
    you are off-track. Everything you do within a process step should be delegated to an entity, and the
    process should at most transform the outputs of one (or more) entities to be a valid input for the next entity.
    """

    STEP_ANNOTATION = "_is_process_step"

    PROCESS_INPUTS_ANNOTATION = "_process_inputs"
    PROCESS_OUTPUTS_ANNOTATION = "_process_outputs"

    @classmethod
    @functools.cache
    def get_events_with_in_type(
        cls, config_class: Type[BaseProcessEntity.In]
    ) -> List[Tuple[Type[WorkEvent], BaseProcessEntity.In]]:
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
    def get_events_with_agent_in(cls) -> List[Tuple[Type[AgentWorkEvent], Agent.In]]:
        return cls.get_events_with_in_type(Agent.In)

    @classmethod
    @functools.cache
    def get_events_with_human_in(cls) -> List[Tuple[Type[HumanWorkEvent], Human.In]]:
        return cls.get_events_with_in_type(Human.In)

    @classmethod
    @functools.cache
    def get_events_with_program_in(cls) -> List[Tuple[Type[ProgramWorkEvent], Program.In]]:
        return cls.get_events_with_in_type(Program.In)

    @classmethod
    @functools.cache
    def get_events_with_process_in(cls) -> List[Tuple[Type[ProcessWorkEvent], Process.In]]:
        return cls.get_events_with_in_type(Process.In)

    @classmethod
    @functools.cache
    def get_events_with_out_type(
        cls, config_class: Type[BaseProcessEntity.Out]
    ) -> List[Tuple[Type[WorkRequestEvent], BaseProcessEntity.Out]]:
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
    def get_events_with_agent_out(cls) -> List[Tuple[Type[AgentWorkRequestEvent], Agent.Out]]:
        return cls.get_events_with_out_type(Agent.Out)

    @classmethod
    @functools.cache
    def get_events_with_human_out(cls) -> List[Tuple[Type[HumanWorkRequestEvent], Human.Out]]:
        return cls.get_events_with_out_type(Human.Out)

    @classmethod
    @functools.cache
    def get_events_with_program_out(cls) -> List[Tuple[Type[ProgramWorkRequestEvent], Program.Out]]:
        return cls.get_events_with_out_type(Program.Out)
