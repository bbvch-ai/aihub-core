from bson import ObjectId

from swiss_ai_hub.core.events.agent.aitl.exception.AgentInTheLoopExceptionEvent import (
    AgentInTheLoopExceptionEvent,
)
from swiss_ai_hub.core.events.agent.aitl.request.AgentInTheLoopRequestEvent import (
    AgentInTheLoopRequestEvent,
)
from swiss_ai_hub.core.events.agent.aitl.response.AgentInTheLoopResponseEvent import (
    AgentInTheLoopResponseEvent,
)
from swiss_ai_hub.core.events.agent.control.start.StartEvent import StartEvent
from swiss_ai_hub.core.topic_managers.agents.AgentTopicManager import AgentTopicManager
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
