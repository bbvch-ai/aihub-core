"""A delegation a model chose as a tool, through real NATS: the worker's steps show in the caller's run under the tool
call, its start event carries the deadline as a TTL, and its answer comes back durably."""

from typing import ClassVar

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.events.agent import (
    AgentInTheLoop,
    DelegatedProgressEvent,
    HumanInTheLoopInput,
    StopEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing.auth_utils import fake_user

from playground.minimal_workflow.agent_in_the_loop_workflow.worker_agent.worker_agent import WorkerAgent
from playground.minimal_workflow.agent_in_the_loop_workflow.worker_agent.worker_agent_config import WorkerAgentConfig
from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner
from swiss_ai_hub.agent.workflow.decorators.step import step


class ToolCallingCaller(Agent):
    """Delegates the way the agent tools capability does: own thread and display, a deadline, a tool call id."""

    name: ClassVar[LocaleString] = LocaleString(en="Tool Calling Caller")
    description: ClassVar[LocaleString] = LocaleString(en="Delegates as a tool call")

    @step()
    async def delegate_step(self, event: UserMessageEvent) -> AgentInTheLoop.request:
        return AgentInTheLoop.invoke(
            agent_class="WorkerAgent",
            agent_id="worker_agent",
            start_event=event,
            share_thread_id=False,
            share_display_id=False,
            timeout_seconds=30,
            tool_call_id="call-1",
        )

    @step()
    async def answered_step(self, answer: AgentInTheLoop.response) -> StopEvent:
        return StopEvent()


class AskingWorker(Agent):
    """A delegate that would ask the user, which no one sees when it was called as a tool."""

    name: ClassVar[LocaleString] = LocaleString(en="Asking Worker")
    description: ClassVar[LocaleString] = LocaleString(en="Asks the user")

    @step()
    async def ask_step(self, event: UserMessageEvent) -> HumanInTheLoopInput.request:
        return HumanInTheLoopInput.invoke(question="Which number?")

    @step()
    async def answered_step(self, answer: HumanInTheLoopInput.response) -> StopEvent:
        return StopEvent()


class AskingCaller(ToolCallingCaller):
    @step()
    async def delegate_step(self, event: UserMessageEvent) -> AgentInTheLoop.request:
        return AgentInTheLoop.invoke(
            agent_class="AskingWorker",
            agent_id="asking_worker",
            start_event=event,
            share_thread_id=False,
            share_display_id=False,
            timeout_seconds=30,
            tool_call_id="call-2",
        )

    @step()
    async def failed_step(self, failure: AgentInTheLoop.exception) -> StopEvent:
        return StopEvent()


def _config(agent: type[Agent], agent_id: str, config_type: type[AgentConfig] = AgentConfig) -> AgentConfig:
    return config_type(
        agent_id=agent_id, agent_class=agent.__name__, name=LocaleString(en=agent_id), description=LocaleString(en="x")
    )


def _message(text: str) -> UserMessageEvent:
    return UserMessageEvent(user=fake_user(), messages=[ChatMessage(role=MessageRole.USER, content=text)])


@pytest.mark.asyncio
async def test_the_worker_s_steps_show_under_the_tool_call_and_its_answer_comes_back():
    worker = AgentTestRunner(
        agent_type=WorkerAgent, agent_config=_config(WorkerAgent, "worker_agent", WorkerAgentConfig)
    )
    caller = AgentTestRunner(agent_type=ToolCallingCaller, agent_config=_config(ToolCallingCaller, "caller"))
    async with worker.test_run(), caller.test_run() as topic:
        await caller.send_event_from_topic(start_event=_message("21"), topic=topic)
        answer = await caller.wait_for_event(AgentInTheLoop.response, timeout=30)
        await caller.wait_for_event(StopEvent)

    progress = [event.event for event in caller.observed_events if isinstance(event.event, DelegatedProgressEvent)]
    assert answer.stop_event.result == 42
    assert {event.tool_call_id for event in progress} == {"call-1"}
    assert {event.agent_class for event in progress} == {"WorkerAgent"}
    assert len(progress) == 2


@pytest.mark.asyncio
async def test_a_delegate_called_as_a_tool_that_asks_the_user_fails_instead():
    worker = AgentTestRunner(agent_type=AskingWorker, agent_config=_config(AskingWorker, "asking_worker"))
    caller = AgentTestRunner(agent_type=AskingCaller, agent_config=_config(AskingCaller, "asking_caller"))
    async with worker.test_run(), caller.test_run() as topic:
        await caller.send_event_from_topic(start_event=_message("hi"), topic=topic)
        failure = await caller.wait_for_event(AgentInTheLoop.exception, timeout=30)

    assert "needs to ask the user" in failure.exception_event.message
