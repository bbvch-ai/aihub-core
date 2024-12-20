from typing import Optional, Annotated


class TopicManager:
    """
    The TopicManager provides a consistent, structured naming scheme for NATS subjects related to agent events
    and discovery operations. By defining conventions for subject strings, it ensures that all components
    (agents, subscribers, orchestrators) can rely on a stable, well-understood pattern to publish and subscribe
    to events.

    ### Why This Class Exists

    In a distributed system where multiple agents produce and consume events, organizing message topics becomes
    critical. Using a conventional pattern:
    - Enhances traceability: Observers can subscribe to all events from a particular agent, a specific agent run,
      or even a single event type (like "display_event" or "control_event").
    - Simplifies filtering: Wildcards in topic segments allow flexible subscriptions—e.g. subscribing to all events
      from all agents, or narrowing down to a specific agent or conversation thread.
    - Improves maintenance: Centralizing topic naming logic in one place makes it easier to adjust conventions
      if needed.

    ### Example Use Cases
    - **Discovery Requests:** Before interacting with a specific agent, a component might send a discovery request
      to learn available capabilities. By using a standardized subject pattern, the discovery mechanism can match
      requests with responses effortlessly.
    - **Event Consumption:** A frontend UI might need to subscribe to all "display_events" from all agents to render
      current states and responses. The TopicManager provides a single call to get that subscription pattern.
    - **Complex Workflows:** Orchestrators or debugging tools might need to capture every control event across all
      agents, or filter down to those belonging to a particular run. The structured patterns here handle these
      scenarios with minimal effort.

    ### Key Concepts
    - **AGENT_TOPIC, DISCOVERY_TOPIC:** Top-level domains indicating that the subject relates to agents or their
      discovery data.
    - **DISPLAY_EVENT, CONTROL_EVENT:** High-level event types. Display events often feed UI or human-facing
      components, while control events represent workflow state changes, errors, or lifecycle signals.
    - **Wildcards:** The use of `'*'` allows broad subscriptions. Tools can start broad and then refine to
      narrower scopes as needed.

    In essence, the TopicManager is a foundational utility that, while simple in nature, vastly reduces the complexity
    of event-driven architectures by standardizing how events are named and accessed.
    """

    AGENT_TOPIC = "agent"
    DISCOVERY_TOPIC = "discovery"

    DISPLAY_EVENT = "display_event"
    CONTROL_EVENT = "control_event"

    def get_agent_discovery_subject_request(
            self,
            call_id: Annotated[str, "Unique identifier linking request and response"],
            agent_class: Annotated[Optional[str], "Agent class filter or '*'"] = "*",
            agent_id: Annotated[Optional[str], "Agent ID filter or '*'"] = "*",
    ) -> str:
        """
        Returns a subject for requesting agent discovery information.
        """
        return f"{self.DISCOVERY_TOPIC}.{self.AGENT_TOPIC}.{agent_class}.{agent_id}.request.{call_id}"

    def get_agent_discovery_subject_response(
            self,
            call_id: str,
            agent_class: Optional[str] = "*",
            agent_id: Optional[str] = "*",
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
        return f"{self.AGENT_TOPIC}.{agent_class}.{agent_id}.{thread_id}.{display_id}.{run_id}.{event_type}.{event_name}.{event_id}"

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

    def get_stream_name_for_all_events_in_agent(self) -> str:
        """Returns the stream name used for all agent events."""
        return f"{self.AGENT_TOPIC}_stream"

    def get_stream_group_for_all_events_in_agent(self) -> str:
        """Returns a queue group name for all agent events."""
        return f"{self.get_stream_name_for_all_events_in_agent()}_queue_group"

    def get_stream_group_for_all_control_events_in_agent(self) -> str:
        """Returns a queue group name for control events only."""
        return f"{self.get_stream_name_for_all_events_in_agent()}_{self.CONTROL_EVENT}_queue_group"

    def get_stream_group_for_all_display_events_in_agent(self) -> str:
        """Returns a queue group name for display events only."""
        return f"{self.get_stream_name_for_all_events_in_agent()}_{self.DISPLAY_EVENT}_queue_group"
