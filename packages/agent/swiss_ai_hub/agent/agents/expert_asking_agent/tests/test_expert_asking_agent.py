# ruff: noqa: E402
from swiss_ai_hub.core.infrastructure import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio
from pathlib import Path

import pytest
from dotenv import load_dotenv
from mongoengine import connect, disconnect
from pytest_bdd import given, scenarios, then, when
from swiss_ai_hub.core.events.agent import (
    BotInTheLoopRequestEvent,
    BotInTheLoopResponderInfo,
    BotInTheLoopResponseEvent,
    TeamsConfig,
)
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoSettings, enable_logging
from swiss_ai_hub.core.testing import async_test
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.agents.expert_asking_agent.events.answer_stop_event import AnswerStopEvent
from swiss_ai_hub.agent.agents.expert_asking_agent.events.ask_expert_start_event import AskExpertStartEvent
from swiss_ai_hub.agent.agents.expert_asking_agent.events.no_answer_stop_event import NoAnswerStopEvent
from swiss_ai_hub.agent.agents.expert_asking_agent.expert_asking_agent import ExpertAskingAgent
from swiss_ai_hub.agent.agents.expert_asking_agent.expert_asking_agent_config import (
    ChannelConfig,
    ExpertAskingAgentConfig,
)
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner

enable_logging()

scenarios("./features/expert_asking_agent.feature")
load_dotenv(Path(__file__).parent / ".env")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def mongo_connection(event_loop):
    """Set up MongoEngine connection for tests."""
    asyncio.set_event_loop(event_loop)
    config = AIHubSettings()
    connect(
        db=config.MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )
    yield
    disconnect()


@pytest.fixture(scope="session")
def expert_asking_agent_config(mongo_connection):
    """Return an ExpertAskingAgentConfig for tests."""
    return ExpertAskingAgentConfig(
        agent_id="test_expert_agent",
        agent_class=ExpertAskingAgent.__name__,
        name=LocaleString(en="Test Expert Asking Agent"),
        description=LocaleString(en="Expert asking agent for tests"),
        llm=LLMConfig(model_name="text-generation/Qwen3-VL-235B-A22B-Instruct"),
        loop_max=2,
        channel_config=ChannelConfig(
            channel_type="teams",
            teams_config=TeamsConfig(
                channel_id="19:test-channel-id@thread.tacv2",
                tenant_id="00000000-0000-0000-0000-000000000000",
                bot_id="00000000-0000-0000-0000-000000000001",
            ),
            slack_config=None,
        ),
        insight_namespace="test_namespace",
    )


def create_expert_responder() -> BotInTheLoopResponderInfo:
    """Create a mock expert responder."""
    return BotInTheLoopResponderInfo(
        user_id="expert_user_123",
        user_name="Expert User",
    )


@pytest.mark.usefixtures("expert_asking_agent_config")
@given("an ExpertAskingAgent runner", target_fixture="agent_runner")
def _(expert_asking_agent_config):
    """Given an ExpertAskingAgent runner."""
    return AgentTestRunner(
        agent_type=ExpertAskingAgent,
        agent_config=expert_asking_agent_config,
    )


@when("a question is asked and the expert provides a sufficient answer")
@async_test
async def _(agent_runner: AgentTestRunner):
    """Send a question and simulate expert providing a sufficient answer."""
    async with agent_runner.test_run(delay_before_stop=300) as topic:
        user = fake_user()

        # Send the initial question to the expert
        await agent_runner.send_event_from_topic(
            topic=topic,
            start_event=AskExpertStartEvent(
                question_to_expert="What is the capital of Switzerland and what is its population?",
                locale="en",
                user=user,
            ),
        )

        # Wait for the BotInTheLoopRequestEvent
        bitl_request = await agent_runner.wait_for_event(BotInTheLoopRequestEvent, timeout=300)

        # Simulate expert providing a clear, complete answer
        await agent_runner.send_event_from_topic(
            topic=bitl_request.topic,
            start_event=BotInTheLoopResponseEvent(
                response="The capital of Switzerland is Bern (de facto capital, officially the Federal City). "
                "Bern has a population of approximately 133,000 in the city proper, and about 420,000 in the "
                "greater metropolitan area as of 2023. Note that Switzerland does not have a de jure capital, "
                "but Bern serves as the seat of government.",
                request_event=bitl_request,
                responder=create_expert_responder(),
            ),
        )


@when("a question is asked and the expert first provides an insufficient answer then a sufficient answer")
@async_test
async def _(agent_runner: AgentTestRunner):
    """Send a question where expert first gives vague answer, then a sufficient one."""
    async with agent_runner.test_run(delay_before_stop=300) as topic:
        user = fake_user()

        # Send the initial question
        await agent_runner.send_event_from_topic(
            topic=topic,
            start_event=AskExpertStartEvent(
                question_to_expert="What are the specific steps to configure SSL certificates in nginx?",
                locale="en",
                user=user,
            ),
        )

        # Wait for first BotInTheLoopRequestEvent
        bitl_request_1 = await agent_runner.wait_for_event(BotInTheLoopRequestEvent, timeout=300)

        # Simulate expert providing an incomplete/vague first answer
        await agent_runner.send_event_from_topic(
            topic=bitl_request_1.topic,
            start_event=BotInTheLoopResponseEvent(
                response="No clue.",
                request_event=bitl_request_1,
                responder=create_expert_responder(),
            ),
        )

        # Wait for the follow-up question (second BotInTheLoopRequestEvent)
        # Clear the previous request from consideration by getting the new one
        bitl_requests = agent_runner.get_events_of_class(BotInTheLoopRequestEvent)
        while len(bitl_requests) < 2:
            await asyncio.sleep(1)  # Yield control to allow agent to process events
            bitl_requests = agent_runner.get_events_of_class(BotInTheLoopRequestEvent)

        bitl_request_2 = bitl_requests[1]

        # Simulate expert providing a complete, detailed answer
        await agent_runner.send_event_from_topic(
            topic=bitl_request_2.topic,
            start_event=BotInTheLoopResponseEvent(
                response="Here are the specific steps to configure SSL in nginx:\n"
                "1. Obtain SSL certificate files (cert.pem and key.pem)\n"
                "2. Place them in /etc/nginx/ssl/\n"
                "3. Edit /etc/nginx/sites-available/your-site with:\n"
                "   server {\n"
                "     listen 443 ssl;\n"
                "     ssl_certificate /etc/nginx/ssl/cert.pem;\n"
                "     ssl_certificate_key /etc/nginx/ssl/key.pem;\n"
                "   }\n"
                "4. Test config with 'nginx -t'\n"
                "5. Reload nginx with 'systemctl reload nginx'",
                request_event=bitl_request_2,
                responder=create_expert_responder(),
            ),
        )


@when("a question is asked and the expert consistently provides insufficient answers")
@async_test
async def _(agent_runner: AgentTestRunner):
    """Send a question where expert consistently gives insufficient answers until max loops."""
    async with agent_runner.test_run(delay_before_stop=300) as topic:
        user = fake_user()

        # Send the initial question
        await agent_runner.send_event_from_topic(
            topic=topic,
            start_event=AskExpertStartEvent(
                question_to_expert="Explain the complete architecture of distributed consensus algorithms.",
                locale="en",
                user=user,
            ),
        )

        # Respond with vague answers up to the max loop count (which is 2 in our config)
        for i in range(2):
            bitl_requests = agent_runner.get_events_of_class(BotInTheLoopRequestEvent)
            while len(bitl_requests) <= i:
                await asyncio.sleep(1)  # Yield control to allow agent to process events
                await agent_runner.wait_for_event(BotInTheLoopRequestEvent, timeout=300)
                bitl_requests = agent_runner.get_events_of_class(BotInTheLoopRequestEvent)

            bitl_request = bitl_requests[i]

            # Provide vague, insufficient responses
            await agent_runner.send_event_from_topic(
                topic=bitl_request.topic,
                start_event=BotInTheLoopResponseEvent(
                    response=f"I'm not sure about that (response {i + 1}).",
                    request_event=bitl_request,
                    responder=create_expert_responder(),
                ),
            )


@then("a BotInTheLoopRequestEvent is present")
def _(agent_runner: AgentTestRunner):
    """Check that a BotInTheLoopRequestEvent was emitted."""
    assert agent_runner.has_event_of_class(BotInTheLoopRequestEvent), "BotInTheLoopRequestEvent was not emitted"


@then("a BotInTheLoopResponseEvent is present")
def _(agent_runner: AgentTestRunner):
    """Check that a BotInTheLoopResponseEvent was observed."""
    assert agent_runner.has_event_of_class(BotInTheLoopResponseEvent), "BotInTheLoopResponseEvent was not emitted"


@then("an AnswerStopEvent is present with the expert answer")
def _(agent_runner: AgentTestRunner):
    """Check that an AnswerStopEvent was emitted with expert answer."""
    assert agent_runner.has_event_of_class(AnswerStopEvent), "AnswerStopEvent was not emitted"
    answer_event = agent_runner.get_event_of_class(AnswerStopEvent)
    assert answer_event.expert_answer, "AnswerStopEvent does not contain expert answer"


@then("multiple BotInTheLoopRequestEvents are present")
def _(agent_runner: AgentTestRunner):
    """Check that multiple BotInTheLoopRequestEvents were emitted (follow-up questions)."""
    events = agent_runner.get_events_of_class(BotInTheLoopRequestEvent)
    assert len(events) >= 2, f"Expected at least 2 BotInTheLoopRequestEvents, got {len(events)}"


@then("a NoAnswerStopEvent is present")
def _(agent_runner: AgentTestRunner):
    """Check that a NoAnswerStopEvent was emitted when max loops reached."""
    assert agent_runner.has_event_of_class(NoAnswerStopEvent), "NoAnswerStopEvent was not emitted"
