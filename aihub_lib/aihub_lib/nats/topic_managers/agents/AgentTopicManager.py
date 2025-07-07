from typing import Annotated

from aihub_lib.nats.topic_managers.TopicManager import TopicManager


class AgentTopicManager(TopicManager):
    AGENT_TOPIC = "agent"

    DISPLAY_EVENT = "display_event"
    CONTROL_EVENT = "control_event"

    def get_agent_discovery_subject_request(
        self,
        call_id: Annotated[str, "Unique identifier linking request and response"],
        agent_class: Annotated[str, "Agent class filter or '*'"] = "*",
        agent_id: Annotated[str, "Agent ID filter or '*'"] = "*",
    ) -> str:
        return f"{self.DISCOVERY_TOPIC}.{self.AGENT_TOPIC}.{agent_class}.{agent_id}.request.{call_id}"

    def get_agent_discovery_subject_response(
        self,
        call_id: str,
        agent_class: Annotated[str, "Agent class filter or '*'"] = "*",
        agent_id: Annotated[str, "Agent ID filter or '*'"] = "*",
    ) -> str:
        """Returns a subject for receiving agent discovery responses."""
        return f"{self.DISCOVERY_TOPIC}.{self.AGENT_TOPIC}.{agent_class}.{agent_id}.response.{call_id}"

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
        """Returns a subject pinpointing a specific event in a given agent run."""
        return (
            f"{self.AGENT_TOPIC}.{agent_class}.{agent_id}"
            f".{thread_id}.{display_id}.{run_id}.{event_type}.{event_name}.{event_id}"
        )

    def get_subject_for_all_events_in_agent(self) -> str:
        """Returns a subject pattern matching all events from all agents."""
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
        """Returns a subject pattern matching all display events from all agents."""
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
        """Returns a subject pattern matching all control events from all agents."""
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
