class TopicManager:
    DISPLAY_EVENT = "display_event"
    CONTROL_EVENT = "control_event"

    def get_subject_for_specific_event_in_agent(
        self,
        agent_class: str,
        agent_id: str,
        thread_id: str,
        display_id: str,
        run_id: str,
        event_type: str,
        event_name: str,
        event_id: str,
    ) -> str:
        return f"agent.{agent_class}.{agent_id}.{thread_id}.{display_id}.{run_id}.{event_type}.{event_name}.{event_id}"

    def get_subject_for_all_events_in_agent(self) -> str:
        return self.get_subject_for_specific_event_in_agent(
            agent_class="*",
            agent_id="*",
            thread_id="*",
            display_id="*",
            run_id="*",
            event_type="*",
            event_name="*",
            event_id="*",
        )

    def get_subject_for_all_display_events_in_agent(self) -> str:
        return self.get_subject_for_specific_event_in_agent(
            agent_class="*",
            agent_id="*",
            thread_id="*",
            display_id="*",
            run_id="*",
            event_type=self.DISPLAY_EVENT,
            event_name="*",
            event_id="*",
        )

    def get_subject_for_all_control_events_in_agent(self) -> str:
        return self.get_subject_for_specific_event_in_agent(
            agent_class="*",
            agent_id="*",
            thread_id="*",
            display_id="*",
            run_id="*",
            event_type=self.CONTROL_EVENT,
            event_name="*",
            event_id="*",
        )

    def get_stream_name_for_all_events_in_agent(self) -> str:
        return "agent_stream"

    def get_stream_group_for_all_events_in_agent(self) -> str:
        return f"{self.get_stream_name_for_all_events_in_agent()}_queue_group"

    def get_stream_group_for_all_control_events_in_agent(self) -> str:
        return f"{self.get_stream_name_for_all_events_in_agent()}_{self.CONTROL_EVENT}_queue_group"

    def get_stream_group_for_all_display_events_in_agent(self) -> str:
        return f"{self.get_stream_name_for_all_events_in_agent()}_{self.DISPLAY_EVENT}_queue_group"
