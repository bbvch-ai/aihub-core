import asyncio
import logging
from typing import Dict

import parse
import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pytest_bdd import scenarios, given, when, then, parsers

from agents_core.runners.AgentTestRunner import AgentTestRunner
from lib_core.i18n.LocaleString import LocaleString
from lib_core.nats.events import StartEvent
from playground.SimpleAgent.Events.EventA import EventA
from playground.SimpleAgent.SimpleAgent import SimpleAgent
from playground.SimpleAgent.SimpleAgentConfig import SimpleAgentConfig

logging.getLogger().setLevel(logging.DEBUG)

scenarios("../tests/features/simple_agent.feature")

@given("a SimpleAgent runner", target_fixture="agent_runner")
def _():
    return AgentTestRunner(
        agent_class=SimpleAgent,
        agent_config=SimpleAgentConfig(
            agent_id="simple_agent",
            name=LocaleString(en="Simple Agent"),
            description=LocaleString(en="This is a very simple agent"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )

@pytest.mark.asyncio
@when(parsers.parse('a the start event is sent with payload "{payload}"'))
async def _(agent_runner: AgentTestRunner, payload: str):
    async with agent_runner.test_run() as topic:
        logging.debug("topic", topic)
        return await agent_runner.send_event_from_topic(
            start_event=StartEvent(messages=[ChatMessage(content=payload, role=MessageRole.USER)]),
            topic=topic,
        )


@then(parsers.parse('a StartEvent is present with payload "{payload}"'))
@pytest.mark.asyncio
async def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_start_event, "Agent did not receive start event"

@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "Agent did not receive start event"

@then(parsers.parse('an EventA event is present with payload "{payload}"'))
def _(agent_runner: AgentTestRunner, payload: str):
    assert agent_runner.get_event_of_type(EventA).payload == payload, "Agent received incorrect data"




    # assert runner.has_start_event, "Agent did not receive start event"
    # assert runner.has_stop_event, "Agent did not receive stop event"
    # assert runner.has_event_of_type(EventA), "Agent did not receive EventA"
    # assert not runner.has_exception_event, "Agent received an exception event"
    # assert runner.get_event_of_type(EventA).payload == "Hello", "Agent received incorrect data"