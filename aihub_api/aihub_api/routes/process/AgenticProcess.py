from dataclasses import dataclass
from typing import TypeVar, Type, Generic

from pydantic import BaseModel

from aihub_lib.nats.events import BaseEvent


# Decorator for regular human-triggered steps
def triggered_by_human(*, route: str):
    def decorator(func):
        setattr(func, "_triggered_by_human", True)
        setattr(func, "_route", route)
        setattr(func, "_is_start_trigger", False) # Differentiator
        return func
    return decorator

# Decorator for human-triggered process start steps
def start_triggered_by_human(*, route: str):
    def decorator(func):
        setattr(func, "_triggered_by_human", True) # Still a human trigger
        setattr(func, "_route", route)
        setattr(func, "_is_start_trigger", True) # Differentiator
        return func
    return decorator

# Decorator for regular agent-triggered steps
def triggered_by_agent(*, agent_class: str, agent_id: str):
    def decorator(func):
        setattr(func, "_triggered_by_agent", True)
        setattr(func, "_agent_class", agent_class)
        setattr(func, "_agent_id", agent_id)
        setattr(func, "_is_start_trigger", False) # Differentiator
        return func
    return decorator

# Decorator for agent-triggered process start steps
def start_triggered_by_agent(*, agent_class: str, agent_id: str):
    def decorator(func):
        setattr(func, "_triggered_by_agent", True) # Still an agent trigger
        setattr(func, "_agent_class", agent_class)
        setattr(func, "_agent_id", agent_id)
        setattr(func, "_is_start_trigger", True) # Differentiator
        return func
    return decorator


TEvent = TypeVar("TEvent", bound=BaseEvent)
TModel = TypeVar("TModel", bound=BaseModel)

class ProcessStep(BaseModel):
    id: str

class HumanProcessStep(ProcessStep, Generic[TModel]):
    responsible_human: str # User ID will go here
    data: TModel # Changed from Type[TModel]

class AgentProcessStep(ProcessStep, Generic[TEvent]):
    responsible_agent: str
    thread_id: str
    display_id: str
    stop_step: TEvent # Assuming this should be an instance too

class Dossier(BaseModel): # Ensure Pydantic models
    name: str
    qualification: str

class AnalyzedDossier(BaseModel): # Ensure Pydantic models
    score: float

class Invitation(BaseModel): # Ensure Pydantic models
    possible_time_slots: str

class Rejection(BaseModel): # Ensure Pydantic models
    feedback: str

class InvitationMail(BaseModel): # Ensure Pydantic models
    text: str

class RejectionMail(BaseModel): # Ensure Pydantic models
    text: str

class AgenticProcess:

    # Example of a start trigger
    @start_triggered_by_human(
        route="/initiate_dossier_analysis", # This route is appended to the controller's base route
    )
    async def initiate_dossier_process(self, step: HumanProcessStep[Dossier]):
        print(f"Process initiated with ID: {step.id} by {step.responsible_human} with dossier: {step.data.name}")
        # ... logic to start a new process ...
        return {"message": "Dossier process initiated", "process_id": step.id, "dossier_name": step.data.name}

    @triggered_by_human(
        route="/dossier", # This route is appended to /process/{process_id}
    )
    async def analyze_dossier(self, step: HumanProcessStep[Dossier]):
        print(f"Analyzing dossier for process ID: {step.id} by {step.responsible_human}")
        # ... logic for analyzing dossier ...
        # Example: return an AnalyzedDossier instance
        return AnalyzedDossier(score=95.5)


    @triggered_by_human(
        route="/dossier/accept", # Appended to /process/{process_id}
    )
    async def accept_dossier(self, step: HumanProcessStep[Invitation]):
        print(f"Accepting dossier for process ID: {step.id} with invitation: {step.data.possible_time_slots} by {step.responsible_human}")
        # ... logic for accepting dossier ...
        return {"message": "Dossier accepted", "process_id": step.id}


    @triggered_by_human(
        route="/dossier/reject", # Appended to /process/{process_id}
    )
    async def reject_dossier(self, step: HumanProcessStep[Rejection]):
        print(f"Rejecting dossier for process ID: {step.id} with feedback: {step.data.feedback} by {step.responsible_human}")
        # ... logic for rejecting dossier ...
        return {"message": "Dossier rejected", "process_id": step.id}
