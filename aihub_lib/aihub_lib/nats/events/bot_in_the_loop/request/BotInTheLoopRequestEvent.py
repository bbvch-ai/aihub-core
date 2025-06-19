from typing import ClassVar, Union

from pydantic import Field

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import ControlEvent
from aihub_lib.nats.topics.agents.AgentTopic import AgentTopic
from aihub_lib.nats.topics.agents.PartialAgentTopic import PartialAgentTopic


class BotInTheLoopRequestEvent(ControlEvent):
    """
    An event asking a human for input, guidance, or approval at a critical juncture in a workflow.

    ### Why HumanInTheLoopRequestEvent?
    In automated workflows, certain decisions may require human validation. This event:
    - Carries a question and a topic indicating where the subsequent response should be sent.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.bitl_request_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.bitl_request_event.description"
    )

    user: UserIdentity = Field(
        ...,
        description="The authenticated user who is requesting the human-in-the-loop interaction.",
    )
    question: str = Field(..., description="The query or prompt presented to the human operator.")
    slack_channel_id: str = Field(
        ..., description="The ID of the Slack channel where the request is sent to.", pattern=r"^C[0-9A-Z]+$"
    )
    topic: Union[PartialAgentTopic, AgentTopic] = Field(
        ...,
        description="A partial or full agent topic specifying the event type and name of the expected response event, ensuring the correct workflow step resumes once the human replies.",
    )
