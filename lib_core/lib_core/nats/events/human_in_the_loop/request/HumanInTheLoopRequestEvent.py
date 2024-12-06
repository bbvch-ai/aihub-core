from pydantic import Field

from agents.Topic import AgentTopic
from agents.Topic.AgentTopic import PartialAgentTopic
from lib.Events import DisplayEvent


class HumanInTheLoopRequestEvent(DisplayEvent):
    question: str = Field(..., description="The question to ask the human")
    topic: PartialAgentTopic | AgentTopic = Field(..., description="The topic to send the response to")
