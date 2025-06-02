from typing import Generic, TypeVar, Type

from pydantic import BaseModel

from aihub_lib.nats.events import BaseEvent

TEvent = TypeVar("TEvent", bound=BaseEvent)
TModel = TypeVar("TModel", bound=BaseModel)

class ProcessStep:
    id: str

class HumanProcessStep(ProcessStep, Generic[TModel]):
    responsible_human: str
    data: Type[TModel]

class AgentProcessStep(ProcessStep, Generic[TEvent]):
    responsible_agent: str
    thread_id: str
    display_id: str
    stop_step: Type[TEvent]

class Dossier:
    name: str
    qualification: str

class AnalyzedDossier:
    score: float

class Invitation:
    possible_time_slots: str

class Rejection:
    feedback: str

class InvitationMail:
    text: str

class RejectionMail:
    text: str


class HiringProcess(Process):

    @start_by_human(
        route="/dossier",
    )
    def analyze_dossier(self, step: HumanProcessStep[Dossier]):
        return trigger_agent_for(
            possible_next_steps=[self.decide_dossier], # Creates empty objects for UI purposes
            start_event=AnalyzeDossierStartEvent(dossier=step.data) # How to start agent
        )
        # Output is received, hence, previous process step is finalized
        # Check if possible_next_steps are all triggered by agent
        # Check whether agent is always the same - CAN'T trigger multiple!
        # Trigger agents

    @triggered_by_agent(
        agent_id=agent_id,
        agent_class=agent_class,
    )
    def decide_dossier(self, analyzed_dossier: AgentProcessStep[AnalyzedDossier]):
        return trigger_human_for(
            possible_next_steps=[self.accept_dossier, self.reject_dossier], # Creates empty objects for UI purposes
            human=oid # Which human to notify and mark as responsible for step
        )

    @triggered_by_human(
        route="/dossier/accept",
    )
    def accept_dossier(self, invitation: HumanProcessStep[Invitation]):
        return trigger_human_for(
            possible_next_steps=[self.accept_dossier, self.reject_dossier],
            human=oid
        )


    @triggered_by_human(
        route="/dossier/reject",
    )
    def reject_dossier(self, rejection: HumanProcessStep[Rejection]):
        return trigger_agent(
            possible_next_steps=[rejection_mail],
            start_event=WriteRejectionMail(dossier=dossier),
            thread_id=thread_id
        )

    @triggered_by_human(
        route="/dossier/invite",
    )
    def invitation_mail(self, mail: HumanProcessStep[InvitationMail]):
        pass

    @triggered_by_agent(
        agent_id=agent_id,
        agent_class=agent_class,
    )
    def rejection_mail(self, mail: AgentProcessStep[RejectionMail]):
        pass
