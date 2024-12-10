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

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(name)s.%(funcName)s] %(levelname)s: %(message)s'
)
logging.getLogger().setLevel(logging.DEBUG)

scenarios("../tests/features/simple_agent.feature")


@pytest.fixture(scope="function")
def context():
    return {}

@given("an test runner")
async def given_agent_config(context):
    runner = AgentTestRunner(
        agent_class=SimpleAgent,
        agent_config=SimpleAgentConfig(
            agent_id="simple_agent",
            name=LocaleString(en="Simple Agent"),
            description=LocaleString(en="This is a very simple agent"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )
    context["runner"] = runner

@when(parsers.parse('a the start event is sent with payload "{payload}"'))
async def send_event(context: Dict, payload: str):
    runner = context["runner"]
    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            start_event=StartEvent(messages=[ChatMessage(content=payload, role=MessageRole.USER)]),
            topic=topic,
        )


@then("runner has start event")
async def start_event(context):
    runner = context["runner"]
    assert runner.has_start_event, "Agent did not receive start event"

@then("runner has stop event")
async def stop_event(context):
    runner = context["runner"]
    assert runner.has_stop_event, "Agent did not receive start event"

@then(parsers.parse('runner has event A with payload "{payload}"'))
async def dummy(context, payload):
    runner = context["runner"]
    assert runner.get_event_of_type(EventA).payload == payload, "Agent received incorrect data"




    # assert runner.has_start_event, "Agent did not receive start event"
    # assert runner.has_stop_event, "Agent did not receive stop event"
    # assert runner.has_event_of_type(EventA), "Agent did not receive EventA"
    # assert not runner.has_exception_event, "Agent received an exception event"
    # assert runner.get_event_of_type(EventA).payload == "Hello", "Agent received incorrect data"