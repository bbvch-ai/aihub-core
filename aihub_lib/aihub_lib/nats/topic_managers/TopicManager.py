from typing import ClassVar

from pydantic import BaseModel


class TopicManager(BaseModel):
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
    - Simplifies filtering: Wildcards in topic segments allow flexible subscriptions - e.g. subscribing to all events
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

    INSTANCE_DISCOVERY_TOPIC: ClassVar[str] = "instance_discovery"
    CLASS_DISCOVERY_TOPIC: ClassVar[str] = "class_discovery"
    RPC_TOPIC: ClassVar[str] = "aihub.rpc"
    CONFIG_RPC_SERVICE: ClassVar[str] = "config"
