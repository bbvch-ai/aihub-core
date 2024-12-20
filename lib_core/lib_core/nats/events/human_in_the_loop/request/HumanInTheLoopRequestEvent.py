from pydantic import Field
from typing import Union

from lib_core.nats.events.display.DisplayEvent import DisplayEvent
from lib_core.nats.topics.agents.AgentTopic import AgentTopic
from lib_core.nats.topics.agents.PartialAgentTopic import PartialAgentTopic


class HumanInTheLoopRequestEvent(DisplayEvent):
    """
    An event asking a human for input, guidance, or approval at a critical juncture in a workflow.

    ### Why HumanInTheLoopRequestEvent?
    In automated workflows, certain decisions may require human validation. This event:
    - Is a `DisplayEvent`, so it can appear in user interfaces.
    - Carries a question and a topic indicating where the subsequent response should be sent.
    """

    question: str = Field(..., description="The query or prompt presented to the human operator.")
    topic: Union[PartialAgentTopic, AgentTopic] = Field(..., description="A partial or full agent topic specifying the event type and name of the expected response event, ensuring the correct workflow step resumes once the human replies.")
