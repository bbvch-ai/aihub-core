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

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(name)s.%(funcName)s] %(levelname)s: %(message)s'
)
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


@given("an test runner", target_fixture="runner")
def given_agent_config():
    runner = AgentTestRunner(
        agent_class=SimpleAgent,
        agent_config=SimpleAgentConfig(
            agent_id="simple_agent",
            name=LocaleString(en="Simple Agent"),
            description=LocaleString(en="This is a very simple agent"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )
    return runner

@when(parsers.parse('a the start event is sent with payload "{payload}"'))
@run_async_test
async def send_event(runner: AgentTestRunner, payload: str):
    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            start_event=StartEvent(messages=[ChatMessage(content=payload, role=MessageRole.USER)]),
            topic=topic,
        )


@then("runner has start event")
def start_event(runner: AgentTestRunner):
    assert runner.has_start_event, "Agent did not receive start event"

@then("runner has stop event")
def stop_event(runner: AgentTestRunner):
    assert runner.has_stop_event, "Agent did not receive stop event"

@then(parsers.parse('runner has event A with payload "{payload}"'))
def dummy(runner: AgentTestRunner, payload):
    assert runner.get_event_of_type(EventA).payload == payload, "Agent received incorrect data"
