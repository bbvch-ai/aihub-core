import asyncio
from pathlib import Path

import pytest
from aihub_lib.agents.step_configs import InsightRetrievalStepConfig
from aihub_lib.generative_ai.retrievers import InsightSourceConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.nats.events.semantic.retriever import RetrievalResponseEvent, RetrievalStartEvent, RetrieverEvent
from aihub_lib.persistence.insight.InsightEntity import InsightCreator, InsightEntity, InsightMessage, InsightSource
from aihub_lib.testing.asyncio_utils.bdd import async_test
from dotenv import load_dotenv
from llama_index.core.base.llms.types import MessageRole
from mongoengine import connect, disconnect
from pytest_bdd import given, parsers, scenarios, then, when

from aihub_agent.agents.InsightRetrievalAgent.configs.InsightRetrievalAgentConfig import InsightRetrievalAgentConfig
from aihub_agent.agents.InsightRetrievalAgent.InsightRetrievalAgent import InsightRetrievalAgent
from aihub_agent.rag.events import InOrderNodeCombinerEvent
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


scenarios("../tests/features/insight_retrieval_agent.feature")
load_dotenv(Path(__file__).parent / ".env")


TEST_INSIGHT_NAMESPACE = "ai_knowledge"
TEST_INSIGHT_AGENT_CLASS = "InsightRetrievalAgent"
TEST_INSIGHT_AGENT_ID = "insight_retrieval_agent"


def create_test_insights(namespace: str, agent_class: str, agent_id: str) -> list[InsightEntity]:
    """Pre-seed MongoDB with test insights for retrieval tests."""
    insights = []
    insight1 = InsightEntity.create_insight(
        question="What is machine learning?",
        expert_answer="Machine learning is a subset of AI that enables systems to learn from data.",
        conversation=[
            InsightMessage(role=MessageRole.USER, content="What is machine learning?"),
            InsightMessage(
                role=MessageRole.ASSISTANT,
                content="Machine learning is a subset of AI that enables systems to learn from data.",
            ),
        ],
        namespace=namespace,
        source=InsightSource(thread_id="test-thread-1", expert_user_id="expert-1", expert_name="Dr. AI Expert"),
        creator=InsightCreator(agent_class=agent_class, agent_id=agent_id, user_id="test-user", user_name="Test User"),
    )
    insights.append(insight1)
    return insights


def delete_test_insights(namespace: str):
    """Cleanup test insights after tests."""
    InsightEntity.objects(namespace=namespace).delete()


@pytest.fixture(scope="session")
def mongo_connection(event_loop):
    """Set up MongoEngine connection for InsightEntity tests."""
    asyncio.set_event_loop(event_loop)
    config = AIHubSettings()
    connect(
        db=config.MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )
    yield
    disconnect()


@pytest.fixture(scope="function")
def test_insights(event_loop, mongo_connection):
    """Setup/teardown test insights for insight retrieval tests."""
    asyncio.set_event_loop(event_loop)
    insights = create_test_insights(
        namespace=TEST_INSIGHT_NAMESPACE,
        agent_class=TEST_INSIGHT_AGENT_CLASS,
        agent_id=TEST_INSIGHT_AGENT_ID,
    )
    yield insights
    try:
        delete_test_insights(namespace=TEST_INSIGHT_NAMESPACE)
    except Exception:
        pass


def build_insight_retrieval_agent_config(
    namespace: str,
    agent_class: str,
    agent_id: str,
) -> InsightRetrievalAgentConfig:
    """Build an InsightRetrievalAgentConfig for testing."""
    return InsightRetrievalAgentConfig(
        agent_id="insight_retrieval_agent",
        agent_class=InsightRetrievalAgent.__name__,
        name=LocaleString(en="Insight Retrieval Agent"),
        description=LocaleString(en="Agent for retrieving expert insights from MongoDB"),
        icon="robot",
        retrieval=InsightRetrievalStepConfig(
            sources=[
                InsightSourceConfig(
                    namespace=namespace,
                    agent_class=agent_class,
                    agent_id=agent_id,
                ),
            ],
        ),
    )


@pytest.fixture(scope="function")
def insight_agent_config(event_loop, test_insights):
    """Set up agent config with insight retriever."""
    asyncio.set_event_loop(event_loop)

    yield build_insight_retrieval_agent_config(
        namespace=TEST_INSIGHT_NAMESPACE,
        agent_class=TEST_INSIGHT_AGENT_CLASS,
        agent_id=TEST_INSIGHT_AGENT_ID,
    )


@pytest.mark.usefixtures("insight_agent_config")
@given("an InsightRetrievalAgent with insight sources configured", target_fixture="agent_runner")
def _(insight_agent_config):
    """Given an InsightRetrievalAgent runner with insight sources configured."""
    return AgentTestRunner(
        agent_type=InsightRetrievalAgent,
        default_agent_config=insight_agent_config,
    )


@given("test insights are pre-seeded in the database")
def _(test_insights):
    """Ensure test insights are pre-seeded in the database (handled by fixture)."""
    assert len(test_insights) > 0, "Test insights were not pre-seeded"


@when(parsers.parse('the user asks "{query}"'))
@async_test
async def _(agent_runner: AgentTestRunner, query: str):
    async with agent_runner.test_run(delay_before_stop=120) as topic:
        await agent_runner.send_event_from_topic(
            topic=topic,
            start_event=RetrievalStartEvent(question=query, locale="en"),
        )


@then("a RetrieverEvent is present with retrieved insight nodes")
def _(agent_runner: AgentTestRunner):
    retriever_event = agent_runner.get_event_of_class(RetrieverEvent)
    assert retriever_event.nodes, "RetrieverEvent did not produce nodes"


@then("the nodes should be combined into a single message")
def _(agent_runner: AgentTestRunner):
    combiner_event = agent_runner.get_event_of_class(InOrderNodeCombinerEvent)
    assert combiner_event.context_message, "InOrderNodeCombinerEvent did not produce context message"


@then("the agent returns an insight response event and stops")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "Agent did not produce StopEvent"
    retrieval_response_event = agent_runner.get_event_of_class(RetrievalResponseEvent)
    assert retrieval_response_event.context_message, "context message is not present in RetrievalResponseEvent"
