from llama_index.core.base.llms.types import ChatMessage

from aihub_lib.nats.events import UserMessageEvent
from aihub_lib.testing.auth_utils.fake_user import fake_user
from aihub_process.agentic_processes.AgenticProcess import AgenticProcess
from aihub_process.delegators.agent.Agent import Agent
from aihub_process.delegators.human.Human import Human
from aihub_process.delegators.program.Program import Program
from aihub_process.process.decorators.process_start import process_start
from aihub_process.process.decorators.process_step import process_step
from playground.AgenticCVProcess.events.agent.AnalyzeCVRequest import AnalyzeCVRequest
from playground.AgenticCVProcess.events.human.AcceptRejectRequest import AcceptRejectRequest
from playground.AgenticCVProcess.events.program.SaveDecisionRequest import SaveDecisionRequest
from playground.AgenticCVProcess.events.program.SubmittedCV import SubmittedCV


class AgenticCVProcess(AgenticProcess):

    @process_start(
        input_from=Program.In(route="/cv", method="POST"),
        delegate_to=Agent.Out(agent_class="LLMWrappingAgent", agent_id="dev_agent"),
    )
    def received_cv_2_analyzed_cv(self, cv: SubmittedCV) -> AnalyzeCVRequest:
        return AnalyzeCVRequest(
            start_event=UserMessageEvent(messages=[ChatMessage(role="user", content=f"Hey {cv.name}!")], user=fake_user())
        )

    @process_step(
        input_from=Agent.In(agent_class="LLMWrappingAgent", agent_id="dev_agent"),
        delegate_to=Human.Out()
    )
    def analyzed_cv_2_accept_reject(self, analyzed_cv: AnalyzeCVRequest.submission) -> AcceptRejectRequest:
        pass

    @process_step(
        input_from=Human.In(route="/cv/accept", method="POST"),
        delegate_to=Program.Out(route="http://my-webserver.com/cv/accept", method="POST")
    )
    def accept_cv(self, accepted_cv: AcceptRejectRequest.accept) -> SaveDecisionRequest:
        return SaveDecisionRequest(
            decision=f"Accepted due to {accepted_cv.reason}"
        )

    @process_step(
        input_from=Human.In(route="/cv/reject", method="POST"),
        delegate_to=Program.Out(route="http://my-webserver.com/cv/reject", method="POST")
    )
    def reject_cv(self, rejected_cv: AcceptRejectRequest.reject) -> SaveDecisionRequest:
        return SaveDecisionRequest(
            decision=f"Rejected due to {rejected_cv.reason}"
        )





















