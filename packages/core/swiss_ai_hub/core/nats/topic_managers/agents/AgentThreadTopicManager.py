from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.core.nats.topic_managers.agents.AgentClassTopicManager import AgentClassTopicManager
from swiss_ai_hub.core.nats.topic_managers.agents.AgentInstanceTopicManager import AgentInstanceTopicManager
from swiss_ai_hub.core.nats.topics.agents.AgentInstanceTopic import AgentInstanceTopic


class AgentThreadTopicManager(AgentInstanceTopicManager):
    """
    The AgentThreadTopicManager refines the event topic naming convention further by focusing on a specific
    conversation thread, display context, and run within a particular agent instance. Extending the
    AgentInstanceTopicManager - which already narrows events down to a given agent_class and agent_id - this class
    adds thread_id, display_id, and run_id to the subject naming pattern.

    ### Why This Class Exists

    As agents handle complex, multi-step interactions (runs) within ongoing conversations (threads), it's useful
    to target events at a more granular level. A single agent instance might serve multiple threads or runs:
    - **Threads:** Represent ongoing conversations or workflows.
    - **Runs:** Represent individual attempts, steps, or calls within that thread.
    - **Display IDs:** Provide an additional layer of grouping or differentiation, often used by UI layers to
      distinguish or group events visually or logically. It doesn't affect agent logic, but helps frontends
      organize and present information more intuitively.

    By selecting thread_id, display_id, and run_id, you can subscribe only to the subset of events that matter to
    a specific UI scenario, troubleshooting session, or user interaction pattern. This granularity ensures that
    subscribers do not need to process irrelevant events from other threads or runs.

    ### Example Use Cases
    - **Chat Frontend:** A UI might subscribe to `display_event` streams for a particular thread and run, ensuring
      it only receives the messages relevant to the current user’s query flow.
    - **Orchestration Tools:** Automated systems can listen to `control_event` topics scoped to a single run and
      thread, allowing them to react only when a certain run within that thread finishes, fails, or hits a
      particular state.
    """

    thread_id: Annotated[str, Field(description="Unique conversation/workflow identifier within the agent instance")]
    display_id: Annotated[str, Field(description="UI-facing grouping ID for events within a thread and run")]
    run_id: Annotated[str, Field(description="Unique run identifier within the thread")]

    def get_subject_for_all_event_in_thread(
        self,
        event_name: Annotated[str, "Name of the event type (e.g. 'start', 'stop', 'error')"],
        event_id: Annotated[str | None, "Specific event instance ID or '*'"] = "*",
    ) -> str:
        """Returns a subject pattern for all events of a given name within this thread."""
        return self.get_subject_for_specific_event_in_agent_instance(
            thread_id=self.thread_id,
            display_id=self.display_id,
            run_id=self.run_id,
            event_type="*",
            event_name=event_name,
            event_id=event_id,
        )

    def get_subject_for_control_event_in_thread(
        self,
        event_name: Annotated[str, "Name of the control event"],
        event_id: Annotated[str | None, "Specific event instance ID or '*'"] = "*",
    ) -> str:
        """Returns a subject pattern for control events of a given name within this thread."""
        return self.get_subject_for_specific_event_in_agent_instance(
            thread_id=self.thread_id,
            display_id=self.display_id,
            run_id=self.run_id,
            event_type=self.CONTROL_EVENT,
            event_name=event_name,
            event_id=event_id,
        )

    def get_subject_for_display_event_in_thread(
        self,
        event_name: Annotated[str, "Name of the display event"],
        event_id: Annotated[str | None, "Specific event instance ID or '*'"] = "*",
    ) -> str:
        """Returns a subject pattern for display events of a given name within this thread."""
        return self.get_subject_for_specific_event_in_agent_instance(
            thread_id=self.thread_id,
            display_id=self.display_id,
            run_id=self.run_id,
            event_type=self.DISPLAY_EVENT,
            event_name=event_name,
            event_id=event_id,
        )

    @classmethod
    def from_agent_instance_topic_manager(
        cls,
        topic_manager: AgentInstanceTopicManager,
        thread_id: Annotated[str, "Thread ID"],
        display_id: Annotated[str, "Display ID for UI grouping"],
        run_id: Annotated[str, "Run ID within the thread"],
    ) -> Self:
        """
        Creates an AgentThreadTopicManager from an existing AgentInstanceTopicManager and additional thread details.
        """
        return cls(
            agent_class=topic_manager.agent_class,
            agent_id=topic_manager.agent_id,
            thread_id=thread_id,
            display_id=display_id,
            run_id=run_id,
        )

    @classmethod
    def from_agent_class_topic_manager(
        cls,
        topic_manager: AgentClassTopicManager,
        agent_id: Annotated[str, "Specific agent ID within the class"],
        thread_id: Annotated[str, "Thread ID"],
        display_id: Annotated[str, "Display ID for UI grouping"],
        run_id: Annotated[str, "Run ID within the thread"],
    ) -> Self:
        """
        Creates an AgentThreadTopicManager from an existing AgentClassTopicManager and additional thread details.
        """
        return cls(
            agent_class=topic_manager.agent_class,
            agent_id=agent_id,
            thread_id=thread_id,
            display_id=display_id,
            run_id=run_id,
        )

    @classmethod
    def from_agent_topic(cls, topic: AgentInstanceTopic) -> Self:
        """Constructs an AgentThreadTopicManager directly from an AgentTopic object."""
        return cls(
            agent_class=topic.agent_class,
            agent_id=topic.agent_id,
            thread_id=topic.thread_id,
            display_id=topic.display_id,
            run_id=topic.run_id,
        )
