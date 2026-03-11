from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.topic_managers.agents.agent_topic_manager import AgentTopicManager
from swiss_ai_hub.core.topics.agents.partial_agent_topic import PartialAgentTopic


class AgentClassTopic(PartialAgentTopic):
    agent_class: Annotated[str, Field(description="The agent's class identifier.")]
    run_id: Annotated[str, Field(description="The run ID within the thread.")]
    thread_id: Annotated[str, Field(description="Unique identifier for the conversation or workflow thread.")]
    display_id: Annotated[str, Field(description="UI-facing grouping ID, used to distinguish or group related runs.")]
    event_type: Annotated[str, Field(description="Type of event (e.g., 'display_event', 'control_event').")]
    event_name: Annotated[
        str, Field(description="Name of the event (e.g., 'StartEvent', 'StopEvent', 'ExceptionEvent, ...').")
    ]
    event_id: Annotated[str, Field(description="Unique identifier for this particular event instance.")]

    def __str__(self) -> str:
        """Returns the full subject string for this agent topic."""
        return (
            f"{AgentTopicManager.AGENT_TOPIC}."
            f"{self.agent_class}."
            f"*."
            f"{self.thread_id}."
            f"{self.display_id}."
            f"{self.run_id}."
            f"{self.event_type}."
            f"{self.event_name}."
            f"{self.event_id}"
        )
