from dataclasses import dataclass
from typing import Annotated, Type, List, Set

from bson import ObjectId
from nats.js import JetStreamContext

from aihub_lib.nats.subscribers.agent.AgentNCSubscriber import AgentNCSubscriber
from aihub_lib.nats.topic_managers.agents.AgentInstanceTopicManager import AgentInstanceTopicManager
from aihub_lib.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from aihub_lib.nats.topic_managers.process.ProcessInstanceTopicManager import ProcessInstanceTopicManager
from aihub_lib.nats.topic_managers.process.ProcessWalkthroughTopicManager import ProcessWalkthroughTopicManager
from aihub_lib.nats.topics.process.ProcessTopic import ProcessTopic

from nats.aio.client import Client as NATS

from aihub_process.agentic_processes.AgenticProcess import AgenticProcess
from aihub_lib.nats.events import AgentWorkRequestEvent, ControlEvent, ProcessStartEvent, AgentWorkEvent
from aihub_lib.nats.topics import AgentTopic
from aihub_process.delegators.AbstractEntityDelegator import AbstractEntityDelegator
from aihub_process.delegators.agent.Agent import Agent


class AgentDelegator(AbstractEntityDelegator):

    def _init__(
            self,
            process: Annotated[Type[AgenticProcess], "The agentic process defining steps and logic."],
            nc: Annotated[NATS, "NATS client for messaging."],
            js: Annotated[
                JetStreamContext,
                "JetStream context for persistent storage and event streams.",
            ],
            topic_manager: Annotated[ProcessInstanceTopicManager, "Manages event subjects."],
            topic: Annotated[Type[ProcessTopic], "Topic under which these events were published"],
    ):
        super()._init__(process, nc, js, topic_manager, topic)
        self.subscriptions = []

    async def start(self):

        for work_event, config in self.process.get_events_with_agent_in():
            control_events = work_event.get_stop_event_type()
            if not control_events:
                continue

            if not isinstance(control_events, (list, tuple)):
                control_events = [control_events]

            for control_event in control_events:
                if control_event is None:
                    continue

                agent_instance_topic_manager = AgentInstanceTopicManager(
                    agent_class=config.agent_class,
                    agent_id=config.agent_id,
                )

                handler = self._get_start_handler(
                    work_event_type=work_event,
                    is_process_start=issubclass(work_event, ProcessStartEvent),
                )

                subscription = AgentNCSubscriber.for_specific_control_event_in_agent(
                    nc=self.nc,
                    topic_manager=agent_instance_topic_manager,
                    handler=handler,
                    event=control_event,
                )
                await subscription.start()
                self.subscriptions.append(subscription)

    async def stop(self):
        for subscription in self.subscriptions:
            await subscription.stop()

    def _get_start_handler(self, work_event_type: Type[AgentWorkEvent], is_process_start: bool):

        async def _handle_process_step_input(
            event: Annotated[ControlEvent, "The incoming agent event to handle."],
            topic: Annotated[AgentTopic, "The parsed topic of the event."],
        ):
            work_event = work_event_type(agent_event=event)

            # Create a new process walkthrough
            if is_process_start:
                walkthrough_topic_manager = ProcessWalkthroughTopicManager.from_process_instance_topic_manager(
                    topic_manager=self.topic_manager,
                    process_walkthrough_id=str(ObjectId())
                )
                subject = walkthrough_topic_manager.get_subject_for_work_event_in_walkthrough(
                    event_name=work_event.event_name,
                    event_id=work_event.event_id,
                )
                await self.js_publisher.publish_event(event, subject)
            else:
                # TODO: Check whether thread belongs to current walkthrough, publish under same walkthrough ID
                pass

        return _handle_process_step_input


    async def _delegate_output(self, event: AgentWorkRequestEvent, out: Agent.Out):
        # Publish event.start_event to agent
        # We must somehow note the thread under which we publish this event such that we
        # can map the response back to this walkthrough
        pass