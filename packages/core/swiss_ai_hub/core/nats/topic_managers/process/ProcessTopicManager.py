from typing import Annotated, ClassVar

from swiss_ai_hub.core.nats.topic_managers.TopicManager import TopicManager


class ProcessTopicManager(TopicManager):
    PROCESS_TOPIC: ClassVar[str] = "process"

    WORK_REQUEST_EVENT: ClassVar[str] = "work_request"
    WORK_EVENT: ClassVar[str] = "work"

    def get_process_config_rpc_subject(
        self,
        process_class: Annotated[str, "Process class identifier or '*' for wildcard"] = "*",
        process_id: Annotated[str, "Process instance ID or '*' for wildcard"] = "*",
    ) -> str:
        """
        Returns the subject for process configuration RPC requests/responses.

        Pattern: aihub.rpc.config.process.{process_class}.{process_id}

        ### Use Cases
        - **Requester**: Use specific process_class and process_id to fetch config for that instance
        - **Responder**: Use wildcards to listen for all config requests: `get_process_config_rpc_subject('*', '*')`
        """
        return f"{self.RPC_TOPIC}.{self.CONFIG_RPC_SERVICE}.{self.PROCESS_TOPIC}.{process_class}.{process_id}"

    def get_process_class_discovery_subject_request(
        self,
        call_id: Annotated[str, "Unique identifier linking request and response"],
        process_class: Annotated[str, "Process class filter or '*'"] = "*",
    ) -> str:
        """Returns a subject for requesting process discovery information for a specific process class."""
        return f"{self.CLASS_DISCOVERY_TOPIC}.{self.PROCESS_TOPIC}.{process_class}.*.request.{call_id}"

    def get_process_class_discovery_subject_response(
        self,
        call_id: Annotated[str, "Unique identifier linking request and response"],
        process_class: Annotated[str, "Process class filter or '*'"] = "*",
    ) -> str:
        """Returns a subject for receiving process discovery information for a specific process class."""
        return f"{self.CLASS_DISCOVERY_TOPIC}.{self.PROCESS_TOPIC}.{process_class}.*.response.{call_id}"

    def get_subject_for_specific_event_in_process(
        self,
        process_class: str,
        process_id: str,
        process_walkthrough_id: str,
        event_type: str,
        event_name: str,
        event_id: str,
    ) -> str:
        """Returns a subject pinpointing a specific event in a given process run."""
        return (
            f"{self.PROCESS_TOPIC}."
            f"{process_class}."
            f"{process_id}."
            f"{process_walkthrough_id}."
            f"{event_type}."
            f"{event_name}."
            f"{event_id}"
        )

    def get_subject_for_all_events_in_process(self) -> str:
        """Returns a subject pattern matching all events from all processes."""
        return self.get_subject_for_specific_event_in_process(
            process_class="*",
            process_id="*",
            process_walkthrough_id="*",
            event_type="*",
            event_name="*",
            event_id="*",
        )

    def get_subject_for_all_work_request_events_in_process(self) -> str:
        """Returns a subject pattern matching all control events from all processes."""
        return self.get_subject_for_specific_event_in_process(
            process_class="*",
            process_id="*",
            process_walkthrough_id="*",
            event_type=self.WORK_REQUEST_EVENT,
            event_name="*",
            event_id="*",
        )

    def get_subject_for_all_work_events_in_process(self) -> str:
        """Returns a subject pattern matching all control events from all processes."""
        return self.get_subject_for_specific_event_in_process(
            process_class="*",
            process_id="*",
            process_walkthrough_id="*",
            event_type=self.WORK_EVENT,
            event_name="*",
            event_id="*",
        )
