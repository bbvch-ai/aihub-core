import asyncio
import functools
import logging

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

def run_async_test(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            asyncio.run(func(*args, **kwargs))
        except Exception as e:
            pytest.fail(f"Failed due to exception: {str(e)}")
    return wrapper


@given("a SimpleAgent runner", target_fixture="agent_runner")def given_agent_config():
    return AgentTestRunner(
        agent_class=SimpleAgent,
        agent_config=SimpleAgentConfig(
            agent_id="simple_agent",
            name=LocaleString(en="Simple Agent"),
            description=LocaleString(en="This is a very simple agent"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )

@when(parsers.parse('a the start event is sent with payload "{payload}"'))
@run_async_test
async def _(agent_runner: AgentTestRunner, payload: str):
    async with agent_runner.test_run() as topic:
        logging.debug("topic", topic)
        await agent_runner.send_event_from_topic(
            start_event=StartEvent(messages=[ChatMessage(content=payload, role=MessageRole.USER)]),
            topic=topic,
        )


@then(parsers.parse('a StartEvent is present with payload "{payload}"'))
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_start_event, "Agent did not receive start event"

@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "Agent did not receive stop event"

@then(parsers.parse('an EventA event is present with payload "{payload}"'))
def _(agent_runner: AgentTestRunner, payload: str):
    assert agent_runner.get_event_of_type(EventA).payload == payload, "Agent received incorrect data"
