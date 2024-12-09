from pydantic import Field

from lib_core.nats.events.display.DisplayEvent import DisplayEvent
from lib_core.nats.topics.agents.AgentTopic import AgentTopic
from lib_core.nats.topics.agents.PartialAgentTopic import PartialAgentTopic


class HumanInTheLoopRequestEvent(DisplayEvent):
    question: str = Field(..., description="The question to ask the human")
    topic: PartialAgentTopic | AgentTopic = Field(..., description="The topic to send the response to")
