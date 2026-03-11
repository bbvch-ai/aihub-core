from typing import Annotated

from llama_index.core.base.llms.types import ChatMessage
from swiss_ai_hub.core.auth.dependencies.dangerous_development_only_auth_handler.dangerous_development_only_auth_settings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from swiss_ai_hub.core.events.agent import UserMessageEvent
from swiss_ai_hub.core.form import (
    CascadeSelect,
    Checkbox,
    DatePicker,
    InputNumber,
    InputText,
    Select,
    SelectButton,
    Slider,
    Textarea,
)
from swiss_ai_hub.core.i18n import LocaleString

from playground.AgenticCVProcess.events.agent.AnalyzeCVRequest import AnalyzeCVRequest
from playground.AgenticCVProcess.events.human.AcceptRejectRequest import AcceptRejectRequest
from playground.AgenticCVProcess.events.human.SubmittedCV import SubmittedCV
from playground.AgenticCVProcess.events.program.SaveDecisionRequest import SaveDecisionRequest
from swiss_ai_hub.process.agentic_processes.agentic_process import AgenticProcess
from swiss_ai_hub.process.delegators.agent.agent import Agent
from swiss_ai_hub.process.delegators.human.human import Human
from swiss_ai_hub.process.delegators.program.program import Program
from swiss_ai_hub.process.process.decorators.process_step import process_step


class AgenticCVProcess(AgenticProcess):
    @process_step()
    async def received_cv_2_analyzed_cv(
        self,
        cv: Annotated[
            SubmittedCV,
            Human.In(
                route="/new-cv",
                method="POST",
                start_form=SubmittedCV(
                    name=InputText(label=LocaleString(en="Name of applicant")),
                    profession=Select(
                        label=LocaleString(en="Profession"),
                        option_label="label",
                        option_value="shortname",
                        options=[
                            {"shortname": "eng", "label": LocaleString(en="Engineer")},
                            {"shortname": "mng", "label": LocaleString(en="Manager")},
                        ],
                    ),
                    application_date=DatePicker(
                        label=LocaleString(en="Application date"),
                    ),
                    level=SelectButton(label="Level", options=["Junior", "Senior"]),
                    match=Slider(
                        label="Match",
                        min=0,
                        max=100,
                        step=1,
                    ),
                    salary=InputNumber(
                        label="Salary Expectations",
                        min=0,
                        max=200_000,
                        step=10_000,
                        mode="currency",
                        show_buttons=True,
                        currency="CHF",
                        locale="de-CH",
                    ),
                    business_area=CascadeSelect(
                        label="Business area",
                        options=[
                            {
                                "name": LocaleString(en="bbv Switzerland"),
                                "code": "bbv-ch",
                                "locations": [
                                    {"name": "Zurich", "code": "bbv-ch-zh"},
                                    {"name": "Lucerne", "code": "bbv-ch-lu"},
                                ],
                            },
                            {
                                "name": LocaleString(en="bbv Greece"),
                                "code": "bbv-gr",
                                "locations": [
                                    {"name": "Thessaloniki", "code": "bbv-gr-th"},
                                ],
                            },
                        ],
                        option_label="name",
                        option_value="code",
                        option_group_label="name",
                        option_group_children=["locations"],
                    ),
                    hire=Checkbox(label=LocaleString(en="Hire $name?")),
                    reasoning=Textarea(
                        condition_if="$get(hire).value",
                        label=LocaleString(en="Why should we hire / not hire this person?"),
                    ),
                ),
            ),
        ],
    ) -> Annotated[AnalyzeCVRequest, Agent.Out(agent_class="LLMWrappingAgent", agent_id="dev_agent")]:
        print("[AgenticCVProcess].received_cv_2_analyzed_cv")
        return AnalyzeCVRequest(
            start_event=UserMessageEvent(
                messages=[ChatMessage(role="user", content=f"Hey {cv.name}!")],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
            )
        )

    @process_step()
    async def analyzed_cv_2_accept_reject(
        self,
        analyzed_cv: Annotated[
            AnalyzeCVRequest.submission, Agent.In(agent_class="LLMWrappingAgent", agent_id="dev_agent")
        ],
    ) -> Annotated[AcceptRejectRequest, Human.Out(user_ids=["some-user-id"])]:
        print("[AgenticCVProcess].analyzed_cv_2_accept_reject", analyzed_cv)
        msg = analyzed_cv.agent_stop_event.output_messages[-1].content
        return AcceptRejectRequest(
            forms=[
                AcceptRejectRequest.accept(
                    display_name=LocaleString(en="This is Accept"),
                    display_description=LocaleString(en="This is description"),
                    reason=InputText(label=LocaleString(en=f"Why do you accept {msg}?")),
                ),
                AcceptRejectRequest.reject(
                    display_name=LocaleString(en="This is Reject"),
                    display_description=LocaleString(en="This is description"),
                    reason=InputText(label=LocaleString(en=f"Why do you reject {msg}?")),
                ),
            ]
        )

    @process_step()
    async def accept_cv(
        self,
        accepted_cv: Annotated[AcceptRejectRequest.accept, Human.In(route="/cv/accept", method="POST")],
    ) -> Annotated[SaveDecisionRequest, Program.Out(endpoint="http://my-webserver.com/cv/accept", method="POST")]:
        print("[AgenticCVProcess].accept_cv", accepted_cv)
        return SaveDecisionRequest(decision=f"Accepted due to {accepted_cv.reason}")

    @process_step()
    async def reject_cv(
        self,
        rejected_cv: Annotated[AcceptRejectRequest.reject, Human.In(route="/cv/reject", method="POST")],
    ) -> Annotated[SaveDecisionRequest, Program.Out(endpoint="http://my-webserver.com/cv/reject", method="POST")]:
        print("[AgenticCVProcess].reject_cv", rejected_cv)
        return SaveDecisionRequest(decision=f"Rejected due to {rejected_cv.reason}")
