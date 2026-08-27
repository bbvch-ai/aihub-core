from bson import ObjectId

from swiss_ai_hub.core.events.agent.aitl.exception.agent_in_the_loop_exception_event import (
    AgentInTheLoopExceptionEvent,
)
from swiss_ai_hub.core.events.agent.aitl.request.agent_in_the_loop_request_event import (
    AgentInTheLoopRequestEvent,
)
from swiss_ai_hub.core.events.agent.aitl.response.agent_in_the_loop_response_event import (
    AgentInTheLoopResponseEvent,
)
from swiss_ai_hub.core.events.agent.control.start.start_event import StartEvent
from swiss_ai_hub.core.topic_managers.agents.agent_topic_manager import AgentTopicManager
from swiss_ai_hub.core.topics import PartialAgentTopic


class AgentInTheLoop:
    """
    A helper for triggering agent-in-the-loop (AITL) steps within a workflow.
    The AITL pattern allows an agent to pause execution and delegate tasks to other agents
    before proceeding with its own workflow.
    The agents may share the same thread, giving the AITL Agent access to the
    current thread context.

    ### Why AgentInTheLoop?
    In automated workflows, certain tasks may require specialized capabilities or domain expertise
    that another agent possesses. AITL steps:
    - Pause at a delegation point
    - Request another agent to perform a specific task
    - Resume execution once the agent response is received

    This class:
    - Provides a convenient `invoke` method to create an `AgentInTheLoopRequestEvent`
    - Defines `request`, `response`, and `exception` attributes representing AITL interactions
    - Manages context sharing between agents to maintain workflow coherence
    """

    request = AgentInTheLoopRequestEvent
    response = AgentInTheLoopResponseEvent
    exception = AgentInTheLoopExceptionEvent

    @classmethod
    def invoke(
        cls,
        agent_class: str,
        agent_id: str,
        start_event: StartEvent,
        share_thread_id: bool = True,
        share_display_id: bool = True,
        share_run_id: bool = False,
    ):
        """
        Create an `AgentInTheLoopRequestEvent` to delegate a task to another agent.

        The `invoke` method constructs the request event and attaches a partial topic indicating where
        the corresponding `AgentInTheLoopResponseEvent` should be directed. This ensures that once
        the other agent completes its task, the workflow can resume from the correct point. It also
        configures context sharing between agents to maintain workflow continuity.
        """
        # `PartialAgentTopic.to_subject` renders a blank segment as the NATS wildcard `*`, so a
        # half-configured delegation would publish to a subject no instance is subscribed to and the
        # caller would wait forever with nothing logged. Fail loudly instead.
        if not agent_class or not agent_id:
            raise ValueError(
                f"Cannot delegate to an incomplete agent reference: "
                f"agent_class={agent_class!r}, agent_id={agent_id!r}. Both are required."
            )

        return cls.request(
            start_event=start_event,
            other_agent_topic=PartialAgentTopic(
                agent_id=agent_id,
                agent_class=agent_class,
                event_type=AgentTopicManager.CONTROL_EVENT,
                event_name=start_event.event_name,
                event_id=str(ObjectId()),
            ),
            share_thread_id=share_thread_id,
            share_display_id=share_display_id,
            share_run_id=share_run_id,
            response=cls.response,
            exception=cls.exception,
        )
