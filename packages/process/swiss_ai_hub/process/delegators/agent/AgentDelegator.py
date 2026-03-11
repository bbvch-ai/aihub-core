import logging
from collections.abc import Awaitable, Callable
from typing import Annotated

from bson import ObjectId
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
from swiss_ai_hub.core.distributor.events.ExternalAgentEvent import ExternalAgentEvent
from swiss_ai_hub.core.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
from swiss_ai_hub.core.events.agent.control.ControlEvent import ControlEvent
from swiss_ai_hub.core.events.process.start.ProcessStartEvent import ProcessStartEvent
from swiss_ai_hub.core.events.process.work.agent.AgentWorkEvent import AgentWorkEvent
from swiss_ai_hub.core.events.process.work.WorkEvent import WorkEvent
from swiss_ai_hub.core.events.process.work_request.agent.AgentWorkRequestEvent import AgentWorkRequestEvent
from swiss_ai_hub.core.events.process.work_request.WorkRequestEvent import WorkRequestEvent
from swiss_ai_hub.core.persistence.messaging.entities.ThreadEntity import AgentInstanceRef, ThreadEntity
from swiss_ai_hub.core.subscribers.agent.AgentNCSubscriber import AgentNCSubscriber
from swiss_ai_hub.core.topic_managers.agents.AgentInstanceTopicManager import AgentInstanceTopicManager
from swiss_ai_hub.core.topic_managers.process.ProcessClassTopicManager import ProcessClassTopicManager
from swiss_ai_hub.core.topics import AgentInstanceTopic
from swiss_ai_hub.core.topics.process.ProcessClassTopic import ProcessClassTopic

from swiss_ai_hub.process.agentic_processes.AgenticProcess import AgenticProcess
from swiss_ai_hub.process.delegators.AbstractEntityDelegator import AbstractEntityDelegator

logger = logging.getLogger(__name__)


class AgentDelegator(AbstractEntityDelegator):
    """
    The agent delegator is responsible to connect agents with a process workflow. It does that by analyzing the
    Agent.In for each step in the process and subscribing to the relevant agent StopEvents. Whenever such a StopEvent
    is received, the delegator wraps it into a WorkEvent and publishes it to the process.
    Vice-versa, for every WorkRequest received from the process, the delegator delegates it to the relevant agent
    by emitting the agents StartEvent.

    The agent delegator must differentiate the cases in which the agents stop event (indicating it has done some work)
    can:
    - Start the process execution (hence, the agent thread/run itself was initially tarted by something
    or someone else, like a user through a direct message), or
    - Can only continue an existing process execution.
    When a StopEvent can start the process execution, the thread_id associated with the StopEvent is irrelevant.
    However, if the StopEvent can not start a process but merely progress the process execution,
    it is mandatory that the agent execution was also started by the same process walkthrough and hence,
    the agents thread is associated with this process walkthrough.

    Why is this important? Well, imagine having an agent with a very generic use-case, like an agent that
    corrects the grammer in a text. It receives a text and returns it with perfect grammar. This agent could be
    used in hundrets of agentic processes. Hence, hundrets of AgentDelegators listen to this agents StopEvents. How
    do we know to which process walkthrough the StopEvent belongs to? Well, when the agent was triggered by a
    process, the thread into which we send the StartEvent is associated with the process walkthrough. Hence, all
    agent delegators ignore all StopEvents that do not belong to the process walkthrough that they themselves know.

    However, let's look at a different scenario: A process starts when an expert asking agent returned a
    KnowledgeMissingStopEvent. The thread associated with this Stop event does certainly NOT belong to any
    process walkthroughs, as the thread is just a direct interaction between the agent and the user.
    However, in this case, the agent delegator must still listen to this KnowledgeMissingStopEvent, and even if it is
    not associated with the current walkthrough, it must still translate the KnowledgeMissingStopEvent into a WorkEvent.

    We can differenciate the two cases easily by checking that the WorkEvent is also a ProcessStartEvent.
    """

    def __init__(
        self,
        process_type: Annotated[type[AgenticProcess], "The agentic process defining steps and logic."],
        nc: Annotated[NATS, "NATS client for messaging."],
        js: Annotated[
            JetStreamContext,
            "JetStream context for persistent storage and event streams.",
        ],
        topic_manager: Annotated[ProcessClassTopicManager, "Manages event subjects."],
        queue_group: str,
    ):
        super().__init__(process_type, nc, js, topic_manager, queue_group)
        self.external_agent_event_distributor = ExternalAgentEventDistributor(
            nc=self.nc, js=self.js, name="ProcessAgentDelegatorExternalAgentEventDistributor"
        )

    async def start(self):
        """
        The agent delegator must find all process steps that are configured wiht Agent.In and
        create a nats subscription to these agents with the relevant stop event.
        """
        await super().start()
        logger.debug(f"Starting agent delegator for process class '{self.process_class}'")

        for work_event, config in self.process_class.get_events_with_agent_in():
            logger.debug(f"Found process step with agent work input: '{work_event.event_name_from_class()}'")
            stop_events = work_event.get_stop_event_type()

            for stop_event in stop_events:
                agent_instance_topic_manager = AgentInstanceTopicManager(
                    agent_class=config.agent_class,
                    agent_id=config.agent_id,
                )

                handler = self.handle_process_step_input_factory(
                    work_event_type=work_event,
                    is_process_start=issubclass(work_event, ProcessStartEvent),
                )

                subscription = AgentNCSubscriber.for_specific_control_event_in_agent_instance(
                    nc=self.nc,
                    topic_manager=agent_instance_topic_manager,
                    handler=handler,
                    event=stop_event,
                    subscriber_name=f"{self.process_class.__name__}AgentDelegator",
                )
                await subscription.start()
                self.subscriptions.append(subscription)

                logger.debug(
                    f"Subscribed to agent '{config.agent_class}' with id "
                    f"'{config.agent_id}' for event '{stop_event.event_name_from_class()}'"
                )

    def handle_process_step_input_factory(
        self, work_event_type: type[AgentWorkEvent], is_process_start: bool
    ) -> Callable[[ControlEvent, AgentInstanceTopic], Awaitable[None]]:
        """
        The agent delegator must differentiate the cases in which the agent can trigger a new process walkthrough
        and the case in which the agent can only continue an existing process walkthrough.

        If the agent can trigger a new process walkthrough, the thread_id associated with the StopEvent is irrelevant.
        Otherwise, we can assume that the thread has an association with the process_walkthrough_id of the process.
        """

        async def _handle_process_step_input(
            event: Annotated[ControlEvent, "The incoming agent event to handle."],
            topic: Annotated[AgentInstanceTopic, "The parsed topic of the event."],
        ):
            logger.debug(f"Handling agent event: {event.event_name}")
            work_event: WorkEvent = work_event_type(
                agent_stop_event=event,
                in_response_to=topic.display_id if not is_process_start else None,
                submitted_by=topic,
            )

            if is_process_start:
                process_walkthrough_id = str(ObjectId())
                logger.debug(f"Creating new walkthrough with ID {process_walkthrough_id}")
            else:
                thread = ThreadEntity.get_thread_by_id(topic.thread_id)

                if thread.process_class != self.process_class.__name__:
                    logger.debug("Ignoring agent event because it does not belong to this process")
                    return

                process_walkthrough_id = thread.process_walkthrough_id
                logger.debug(f"Continuing existing walkthrough with ID {process_walkthrough_id}")

            await self._publish_work_event(
                work_event=work_event,
                process_walkthrough_id=process_walkthrough_id,
            )

        return _handle_process_step_input

    async def handle_process_step_output(self, event: WorkRequestEvent, topic: ProcessClassTopic):
        """
        When receiving a AgentWorkRequestEvent, we can simply create a new thread and send the start event
        that is part of te AgentWorkReqeustEvent to the appropriate agent as an external event.
        """
        if not isinstance(event, AgentWorkRequestEvent):
            return

        logger.debug(f"Delegating agent output to external agent: {event.agent_class} with id {event.agent_id}")
        thread_id = ObjectId()

        ThreadEntity.create_process_thread(
            name=self.process_class.__name__,
            agent=AgentInstanceRef(agent_class=event.agent_class, agent_id=event.agent_id),
            thread_id=thread_id,
            process_class=self.process_class.__name__,
            process_id=event.process_id,
            process_walkthrough_id=topic.process_walkthrough_id,
        )

        external_event = ExternalAgentEvent(
            thread_id=str(thread_id),
            display_id=event.event_id,
            event=event.start_event,
        )

        await self.external_agent_event_distributor.distribute_event(external_event=external_event)
