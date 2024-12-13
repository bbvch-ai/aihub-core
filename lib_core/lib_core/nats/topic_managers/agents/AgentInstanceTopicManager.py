from typing import Optional

from lib_core.nats.topic_managers.TopicManager import TopicManager


class AgentInstanceTopicManager(TopicManager):
    def __init__(self, agent_class: str, agent_id: str):
        super().__init__()
        self.agent_class = agent_class
        self.agent_id = agent_id

    def get_subject_for_streaming_all_events_within_agent(self) -> str:
        return self.get_subject_for_specific_event_in_agent(
            agent_class=self.agent_class,
            agent_id=self.agent_id,
            thread_id="*",
            display_id="*",
            run_id="*",
            event_type="*",
            event_name="*",
            event_id="*",
        )

    def get_agent_discovery_subject_request(self, call_id: str, agent_class: Optional[str] = None, agent_id: Optional[str] = None) -> str:
        return super().get_agent_discovery_subject_request(
            agent_class=agent_class or self.agent_class,
            agent_id=agent_id or self.agent_id,
            call_id=call_id,
        )

    def get_agent_discovery_subject_response(self, call_id: str, agent_class: Optional[str] = None, agent_id: Optional[str] = None) -> str:
        return super().get_agent_discovery_subject_response(
            agent_class=agent_class or self.agent_class,
            agent_id=agent_id or self.agent_id,
            call_id=call_id,
        )

    def get_stream_name_for_all_events_within_agent(self) -> str:
        return f"agent_{self.agent_class}_{self.agent_id}_stream"

    def get_stream_group_for_all_control_events_within_agent(self) -> str:
        return f"{self.get_stream_name_for_all_events_within_agent()}_{self.CONTROL_EVENT}_queue_group"

    def get_stream_group_for_all_display_events_within_agent(self) -> str:
        return f"{self.get_stream_name_for_all_events_within_agent()}_{self.DISPLAY_EVENT}_queue_group"

    def get_subject_for_specific_event_in_agent_instance(
        self,
        thread_id: str,
        display_id: str,
        run_id: str,
        event_type: str,
        event_name: str,
        event_id: str,
    ) -> str:
        return self.get_subject_for_specific_event_in_agent(
            agent_class=self.agent_class,
            agent_id=self.agent_id,
            thread_id=thread_id,
            display_id=display_id,
            run_id=run_id,
            event_type=event_type,
            event_name=event_name,
            event_id=event_id,
        )

    def get_subject_for_everything_within_agent_instance(self) -> str:
        return self.get_subject_for_specific_event_in_agent_instance(
            thread_id="*",
            display_id="*",
            run_id="*",
            event_type="*",
            event_name="*",
            event_id="*",
        )

    def get_subject_for_all_display_events_within_agent_instance(self) -> str:
        return self.get_subject_for_specific_event_in_agent_instance(
            thread_id="*",
            display_id="*",
            run_id="*",
            event_type=self.DISPLAY_EVENT,
            event_name="*",
            event_id="*",
        )

    def get_subject_for_all_control_events_within_agent_instance(self) -> str:
        return self.get_subject_for_specific_event_in_agent_instance(
            thread_id="*",
            display_id="*",
            run_id="*",
            event_type=self.CONTROL_EVENT,
            event_name="*",
            event_id="*",
        )
