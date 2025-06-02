from banks import ChatMessage
from pydantic import BaseModel

from aihub_api.routes.process.AgenticProcess import AgenticProcess, start_triggered_by_human, HumanProcessStep, \
    triggered_by_human, TriggerAgentFor, triggered_by_agent, AgentProcessStep, TriggerHumanFor
from aihub_lib.nats.events import LLMStopEvent, UserMessageEvent
from aihub_lib.testing.auth_utils.fake_user import fake_user


class Dossier(BaseModel):
    name: str
    qualification: str

class AnalyzedDossier(BaseModel):
    score: float

class Invitation(BaseModel):
    possible_time_slots: str

class Rejection(BaseModel):
    feedback: str

class InvitationMail(BaseModel):
    text: str

class RejectionMail(BaseModel):
    text: str

class AgenticCVProcess(AgenticProcess):

    @start_triggered_by_human(
        route="/initiate_dossier_analysis",
    )
    async def initiate_dossier_process(self, step: HumanProcessStep[Dossier]) -> TriggerAgentFor:
        print(f"Process initiated with ID: {step.id} by {step.responsible_human} with dossier: {step.data.name}")
        return TriggerAgentFor(
            possible_next_steps=[self.decide_dossier],
            start_event=UserMessageEvent(messages=[ChatMessage(role="user", content=f"Hey! {step.dossier.name}")], user=fake_user())
        )

    @triggered_by_agent(
        agent_id="dev_agent",
        agent_class="LLMWrappingAgent",
    )
    def decide_dossier(self, analyzed_dossier: AgentProcessStep[LLMStopEvent]) -> TriggerHumanFor:
        print("Received analyzed dossier", analyzed_dossier)
        return TriggerHumanFor(
            possible_next_steps=[self.accept_dossier, self.reject_dossier],
            human="unknown oid"
        )

    @triggered_by_human(
        route="/dossier",
    )
    async def analyze_dossier(self, step: HumanProcessStep[Dossier]):
        print(f"Analyzing dossier for process ID: {step.id} by {step.responsible_human}")
        return AnalyzedDossier(score=95.5)

    @triggered_by_human(
        route="/dossier/accept",
    )
    async def accept_dossier(self, step: HumanProcessStep[Invitation]):
        print(f"Accepting dossier for process ID: {step.id} with invitation: {step.data.possible_time_slots} by {step.responsible_human}")
        return {"message": "Dossier accepted", "process_id": step.id}

    @triggered_by_human(
        route="/dossier/reject",
    )
    async def reject_dossier(self, step: HumanProcessStep[Rejection]):
        print(f"Rejecting dossier for process ID: {step.id} with feedback: {step.data.feedback} by {step.responsible_human}")
        return {"message": "Dossier rejected", "process_id": step.id}