import functools
from typing import List, Tuple, Type

from aihub_lib.nats.events import AgentWorkEvent, WorkEvent, ProgramWorkEvent, HumanWorkEvent, WorkRequestEvent, \
    AgentWorkRequestEvent, HumanWorkRequestEvent, ProgramWorkRequestEvent
from aihub_lib.nats.workflow.DispatchableWorkflow import DispatchableWorkflow
from aihub_process.delegators.AbstractProcessEntity import BaseProcessEntity
from aihub_process.delegators.agent.Agent import Agent
from aihub_process.delegators.human.Human import Human
from aihub_process.delegators.program.Program import Program


class AgenticProcess(DispatchableWorkflow):
    STEP_ANNOTATION = "_is_process_step"

    @classmethod
    @functools.cache
    def get_events_with_in_type(cls, config_class: Type[BaseProcessEntity.In]) -> List[Tuple[Type[WorkEvent], BaseProcessEntity.In]]:
        """
        Scans all process steps to find inputs matching a specific configuration class.
        This now iterates over the pre-processed list stored on each step method.
        """
        found_events = []
        for step_method in cls.get_steps():
            # Iterate through the list of (event, config) tuples stored by the decorator
            for event_type, config_instance in getattr(step_method, "_process_inputs", []):
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
    def get_events_with_out_type(cls, config_class: Type[BaseProcessEntity.Out]) -> List[Tuple[Type[WorkRequestEvent], BaseProcessEntity.Out]]:
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