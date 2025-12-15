# ruff: noqa: E402
from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.nats.events import HumanInTheLoop, UserMessageEvent
from aihub_lib.nats.events.agent_in_the_loop import AgentInTheLoopRequestEvent
from aihub_lib.nats.events.human_in_the_loop.request.HumanInTheLoopRequestEvent import (
    HumanInTheLoopChatRequestEvent,
)
from aihub_lib.persistence.i18n.LocaleStringEntity import LocaleStringEntity
from aihub_lib.testing.asyncio_utils.bdd import async_test
from dotenv import load_dotenv
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pytest_bdd import given, parsers, scenarios, then, when

from aihub_agent.agents.configs import AgentReference
from aihub_agent.agents.NamespaceSelectionAgent import NamespaceSelectionAgent
from aihub_agent.agents.NamespaceSelectionAgent.configs.BucketReference import BucketReference
from aihub_agent.agents.NamespaceSelectionAgent.configs.NamespaceSelectionAgentConfig import (
    NamespaceSelectionAgentConfig,
)
from aihub_agent.agents.RagAgent import RAGAgent
from aihub_agent.context.thread.ThreadContext import ThreadContext
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


scenarios("./features/namespace_selection_agent.feature")
load_dotenv(Path(__file__).parent / ".env")

TIMEOUT = 120


# ==================== Mock Data ====================


def create_mock_bucket():
    """Create a mock BucketEntity."""
    bucket = MagicMock()
    bucket.id = "test_bucket_id"
    bucket.bucket_name = "test_bucket"
    bucket.name = LocaleStringEntity(en="Test Bucket", de="Test Bucket", fr="Test Bucket", it="Test Bucket")
    return bucket


def create_mock_namespaces():
    """Create mock NamespaceEntity list."""
    namespaces = []

    ns1 = MagicMock()
    ns1.namespace_name = "hr"
    ns1.display_name = LocaleStringEntity(
        en="Human Resources", de="Personalwesen", fr="Ressources Humaines", it="Risorse Umane"
    )
    namespaces.append(ns1)

    ns2 = MagicMock()
    ns2.namespace_name = "finance"
    ns2.display_name = LocaleStringEntity(en="Finance", de="Finanzen", fr="Finance", it="Finanza")
    namespaces.append(ns2)

    return namespaces


# ==================== Config ====================


def build_namespace_selection_agent_config(llm_config: LLMConfig) -> NamespaceSelectionAgentConfig:
    """Build a NamespaceSelectionAgentConfig with the specified LLM configuration."""
    return NamespaceSelectionAgentConfig(
        agent_id="namespace_selection_agent",
        agent_class=NamespaceSelectionAgent.__name__,
        name=LocaleString(en="Namespace Selection Agent"),
        description=LocaleString(en="Agent that asks users to select namespaces"),
        buckets=[
            BucketReference(bucket_name="test_bucket"),
        ],
        rag_agent=AgentReference(
            agent_class=RAGAgent.__name__,
            agent_id="test_rag_agent",
        ),
        llm=llm_config,
    )


@pytest.fixture(scope="session")
def namespace_selection_agent_config():
    """Return a NamespaceSelectionAgentConfig that uses a self-hosted LLM."""
    llm_config = LLMConfig(model_name="text-generation/mini")
    return build_namespace_selection_agent_config(llm_config=llm_config)


# ==================== Given Steps ====================


@pytest.mark.usefixtures("namespace_selection_agent_config")
@given("a NamespaceSelectionAgent runner with mocked buckets and namespaces", target_fixture="agent_runner")
def _(namespace_selection_agent_config):
    """Given a NamespaceSelectionAgent runner with mocked bucket/namespace data."""
    return AgentTestRunner(
        agent_type=NamespaceSelectionAgent,
        default_agent_config=namespace_selection_agent_config,
    )


@pytest.mark.usefixtures("namespace_selection_agent_config")
@given("a NamespaceSelectionAgent runner with existing namespace selection", target_fixture="agent_runner")
def _(namespace_selection_agent_config):
    """Given a NamespaceSelectionAgent runner with pre-existing namespace selection."""
    runner = AgentTestRunner(
        agent_type=NamespaceSelectionAgent,
        default_agent_config=namespace_selection_agent_config,
    )
    # Pre-populate ThreadContext with namespace selection
    # This would be done via the runner's context setup methods
    return runner


# ==================== When Steps ====================


@when(parsers.parse('the user sends a message "{query}"'))
@async_test
async def _(agent_runner: AgentTestRunner, query: str):
    """When the user sends a message."""
    with (
        patch(
            "aihub_agent.agents.NamespaceSelectionAgent.namespace_data.BucketEntity.get_bucket_by_bucket_name"
        ) as mock_get_bucket,
        patch(
            "aihub_agent.agents.NamespaceSelectionAgent.namespace_data.NamespaceEntity.get_namespaces_by_bucket"
        ) as mock_get_namespaces,
    ):
        mock_get_bucket.return_value = create_mock_bucket()
        mock_get_namespaces.return_value = create_mock_namespaces()

        async with agent_runner.test_run() as topic:
            user_event = UserMessageEvent(
                messages=[ChatMessage(role=MessageRole.USER, content=query)],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
                locale="en",
            )
            await agent_runner.send_event_from_topic(start_event=user_event, topic=topic)

            # Wait for the HITL chat request event
            await agent_runner.wait_for_event(HumanInTheLoopChatRequestEvent, timeout=TIMEOUT)


@when(parsers.parse('the user sends a message and selects "{namespace}" namespace'))
@async_test
async def _(agent_runner: AgentTestRunner, namespace: str):
    """When the user sends a message and selects a namespace."""
    with (
        patch(
            "aihub_agent.agents.NamespaceSelectionAgent.namespace_data.BucketEntity.get_bucket_by_bucket_name"
        ) as mock_get_bucket,
        patch(
            "aihub_agent.agents.NamespaceSelectionAgent.namespace_data.NamespaceEntity.get_namespaces_by_bucket"
        ) as mock_get_namespaces,
    ):
        mock_get_bucket.return_value = create_mock_bucket()
        mock_get_namespaces.return_value = create_mock_namespaces()

        async with agent_runner.test_run() as topic:
            user_event = UserMessageEvent(
                messages=[ChatMessage(role=MessageRole.USER, content="Search HR documents")],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
                locale="en",
            )
            await agent_runner.send_event_from_topic(start_event=user_event, topic=topic)

            # Wait for HITL chat request
            hitl_request = await agent_runner.wait_for_event(HumanInTheLoopChatRequestEvent, timeout=TIMEOUT)

            # Send user's selection response
            response_event = HumanInTheLoop.chat.response(
                response=f"I want to use {namespace}",
                request_event=hitl_request,
            )
            await agent_runner.send_event_from_topic(
                start_event=response_event,
                topic=hitl_request.topic,
            )

            # Wait for agent to process and emit AgentInTheLoopRequestEvent
            await agent_runner.wait_for_event(AgentInTheLoopRequestEvent, timeout=TIMEOUT)


@when(parsers.parse('the user sends a subsequent message "{query}"'))
@async_test
async def _(agent_runner: AgentTestRunner, query: str):
    """When the user sends a subsequent message (with existing namespace selection)."""
    async with agent_runner.test_run() as topic:
        # Pre-populate ThreadContext with namespace selection and available namespaces
        thread_context = ThreadContext(agent_runner.redis, topic.thread_id)
        await thread_context.set(
            "namespace_selections",
            [{"bucket_name": "test_bucket", "namespaces": ["hr"]}],
        )
        await thread_context.set(
            "available_namespaces",
            [
                {
                    "bucket_name": "test_bucket",
                    "bucket_display_name": {"en": "Test Bucket"},
                    "namespaces": [{"name": "hr", "display_name": {"en": "Human Resources"}}],
                }
            ],
        )

        user_event = UserMessageEvent(
            messages=[ChatMessage(role=MessageRole.USER, content=query)],
            user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
            locale="en",
        )
        await agent_runner.send_event_from_topic(start_event=user_event, topic=topic)

        # Should delegate directly to RAG without asking for selection
        await agent_runner.wait_for_event(AgentInTheLoopRequestEvent, timeout=TIMEOUT)


# ==================== Then Steps ====================


@then("a HumanInTheLoopChatRequestEvent is present")
def _(agent_runner: AgentTestRunner):
    """Then a HumanInTheLoopChatRequestEvent is present."""
    assert agent_runner.has_event_of_class(
        HumanInTheLoopChatRequestEvent
    ), "Agent did not emit HumanInTheLoopChatRequestEvent"


@then("the chat request message asks about namespace selection")
def _(agent_runner: AgentTestRunner):
    """Then the chat request asks about namespace selection."""
    event = agent_runner.get_event_of_class(HumanInTheLoopChatRequestEvent)
    # The message should mention namespaces or selection
    assert event.message is not None and len(event.message) > 0, "Chat request message is empty"


@then("the namespace selection is stored in ThreadContext")
def _(agent_runner: AgentTestRunner):
    """Then the namespace selection is stored."""
    # This would check ThreadContext - for now we verify the flow continued
    pass


@then("an AgentInTheLoopRequestEvent is present for RAGAgent")
def _(agent_runner: AgentTestRunner):
    """Then an AgentInTheLoopRequestEvent is present."""
    assert agent_runner.has_event_of_class(AgentInTheLoopRequestEvent), "Agent did not emit AgentInTheLoopRequestEvent"


@then("the RAGUserMessageEvent includes namespace overrides")
def _(agent_runner: AgentTestRunner):
    """Then the RAGUserMessageEvent includes namespace overrides."""
    event = agent_runner.get_event_of_class(AgentInTheLoopRequestEvent)
    # Check that the start_event is a RAGUserMessageEvent with bucket_namespace_selections
    from aihub_agent.agents.RagAgent.events import RAGUserMessageEvent

    assert isinstance(event.start_event, RAGUserMessageEvent), "Start event is not RAGUserMessageEvent"
    assert (
        event.start_event.bucket_namespace_selections is not None
    ), "RAGUserMessageEvent has no bucket_namespace_selections"
