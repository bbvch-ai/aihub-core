from typing import Annotated, override

from pydantic import Field

from swiss_ai_hub.core.nats.topic_managers.agents.AgentClassTopicManager import AgentClassTopicManager


class AgentInstanceTopicManager(AgentClassTopicManager):
    """
    The AgentInstanceTopicManager narrows down event subscription and publishing
    to a specific agent instance - identified by its agent_class and agent_id.
    Building on top of the more general TopicManager, it provides methods to:
    - Request and receive discovery information filtered by a particular agent instance.
    - Target all events, or selectively display or control events, coming from this one agent instance.
    - Create subject patterns that include thread, display, and run IDs, but with the agent_class and agent_id
      already fixed. This simplifies subscribing to and managing events for a single, identifiable agent.

    ### Why This Class Exists

    In a multi-agent environment, where various agents of different classes and IDs produce and consume events,
    focusing on a single agent instance is often necessary. For instance, you might have multiple agents of the
    same class (e.g., different chatbots or service bots), each identified by a unique agent_id. By using the
    AgentInstanceTopicManager, you can:
    - Query discovery info specifically for that instance.
    - Listen to all or selected types of events from that one agent instance.
    - Compose more specific topic managers, like AgentThreadTopicManager, that build on this base filtering.

    ### Use Cases
    - **Dedicated Monitoring:** A dashboard might show all events from a single critical agent instance.
    - **Per-Agent Control:** An orchestrator that needs to send requests
      or receive responses only from a known agent instance.
    """

    agent_id: Annotated[str, Field(description="Unique agent instance ID")]

    def get_agent_config_rpc_subject_for_instance(self) -> str:
        """
        Returns the RPC subject for fetching this agent instance's configuration.

        Uses the instance's own agent_class and agent_id to build the subject.
        """
        return self.get_agent_config_rpc_subject(self.agent_class, self.agent_id)

    def get_agent_instance_discovery_subject_request(
        self,
        call_id: Annotated[str, "Identifier linking request and response"],
        agent_class: str | None = None,
        agent_id: str | None = None,
    ) -> str:
        """
        Returns a subject for requesting discovery info about this agent instance (or a provided override).
        If agent_class/agent_id are not specified, it uses the instance's own identifiers.
        """
        return super().get_agent_instance_discovery_subject_request(
            agent_class=agent_class or self.agent_class,
            agent_id=agent_id or self.agent_id,
            call_id=call_id,
        )

    def get_agent_instance_discovery_subject_response(
        self,
        call_id: Annotated[str, "Identifier linking request and response"],
        agent_class: str | None = None,
        agent_id: str | None = None,
    ) -> str:
        """
        Returns a subject for receiving agent discovery responses for this agent instance (or a provided override).
        If agent_class/agent_id are not specified, it uses the instance's own identifiers.
        """
        return super().get_agent_instance_discovery_subject_response(
            agent_class=agent_class or self.agent_class,
            agent_id=agent_id or self.agent_id,
            call_id=call_id,
        )

    def get_subject_for_streaming_all_events_within_agent(self) -> str:
        """Returns a subject pattern for all events originating from this agent instance."""
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

    def get_subject_for_specific_event_in_agent_instance(
        self,
        thread_id: Annotated[str, "Thread ID within this agent instance"],
        display_id: Annotated[str, "Display ID for UI/grouping"],
        run_id: Annotated[str, "Run ID within the thread"],
        event_type: Annotated[str, "Event type (e.g., display_event, control_event)"],
        event_name: Annotated[str, "Specific event name"],
        event_id: Annotated[str, "Event instance ID"],
    ) -> str:
        """Returns a subject for a specific event from this agent instance, narrowed by thread, display, and run."""
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
        """Returns a subject pattern for all events in this agent instance, regardless of thread, display, or run."""
        return self.get_subject_for_specific_event_in_agent_instance(
            thread_id="*",
            display_id="*",
            run_id="*",
            event_type="*",
            event_name="*",
            event_id="*",
        )

    def get_subject_for_all_display_events_within_agent_instance(self) -> str:
        """Returns a subject pattern matching all display events within this agent instance."""
        return self.get_subject_for_specific_event_in_agent_instance(
            thread_id="*",
            display_id="*",
            run_id="*",
            event_type=self.DISPLAY_EVENT,
            event_name="*",
            event_id="*",
        )

    def get_subject_for_all_control_events_within_agent_instance(self) -> str:
        """Returns a subject pattern matching all control events within this agent instance."""
        return self.get_subject_for_specific_event_in_agent_instance(
            thread_id="*",
            display_id="*",
            run_id="*",
            event_type=self.CONTROL_EVENT,
            event_name="*",
            event_id="*",
        )

    @override
    def get_subject_for_all_control_events(self) -> str:
        return self.get_subject_for_all_control_events_within_agent_instance()

    def get_subject_for_all_events_in_agent(self) -> str:
        """Returns a subject pattern matching all events from all agents."""
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

    def get_subject_for_all_display_events_in_agent(self) -> str:
        """Returns a subject pattern matching all display events from all agents."""
        return self.get_subject_for_specific_event_in_agent(
            agent_class=self.agent_class,
            agent_id=self.agent_id,
            thread_id="*",
            display_id="*",
            run_id="*",
            event_type=self.DISPLAY_EVENT,
            event_name="*",
            event_id="*",
        )
