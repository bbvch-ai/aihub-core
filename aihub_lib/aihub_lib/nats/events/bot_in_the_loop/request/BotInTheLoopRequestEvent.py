from typing import Union

from pydantic import Field

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

    question: str = Field(..., description="The query or prompt presented to the human operator.")
    topic: Union[PartialAgentTopic, AgentTopic] = Field(
        ...,
        description="A partial or full agent topic specifying the event type and name of the expected response event, ensuring the correct workflow step resumes once the human replies.",
    )
