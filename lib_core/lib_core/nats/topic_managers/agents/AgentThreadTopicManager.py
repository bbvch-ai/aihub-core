from typing import Optional

from lib_core.nats.topic_managers.agents.AgentInstanceTopicManager import (
    AgentInstanceTopicManager,
)


class AgentThreadTopicManager(AgentInstanceTopicManager):
    def __init__(
        self,
        agent_class: str,
        agent_id: str,
        thread_id: str,
        display_id: str,
        run_id: str,
    ):
        super().__init__(agent_class=agent_class, agent_id=agent_id)
        self.thread_id = thread_id
        self.display_id = display_id
        self.run_id = run_id

    def get_subject_for_control_event_in_thread(self, event_name: str, event_id: Optional[str] = "*") -> str:
        return self.get_subject_for_specific_event_in_agent_instance(
            thread_id=self.thread_id,
            display_id=self.display_id,
            run_id=self.run_id,
            event_type=self.CONTROL_EVENT,
            event_name=event_name,
            event_id=event_id,
        )

    def get_subject_for_display_event_in_thread(self, event_name: str, event_id: Optional[str] = "*") -> str:
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
        thread_id: str,
        display_id: str,
        run_id: str,
    ) -> "AgentThreadTopicManager":
        return cls(
            agent_class=topic_manager.agent_class,
            agent_id=topic_manager.agent_id,
            thread_id=thread_id,
            display_id=display_id,
            run_id=run_id,
        )
