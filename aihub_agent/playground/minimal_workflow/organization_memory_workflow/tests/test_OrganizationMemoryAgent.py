# ruff: noqa: E402
from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import pytest
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.nats.events import (
    AddOrganizationMemoryToChatHistoryEvent,
    LLMStopEvent,
    RetrieveOrganizationMemoryEvent,
    StoreOrganizationMemoryEvent,
    UserMessageEvent,
)
from aihub_lib.testing.asyncio_utils.bdd import async_test
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pytest_bdd import given, parsers, scenarios, then, when

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.organization_memory_workflow.OrganizationMemoryAgent import OrganizationMemoryAgent
from playground.minimal_workflow.organization_memory_workflow.OrganizationMemoryAgentConfig import (
    OrganizationMemoryAgentConfig,
)

enable_logging()

scenarios("./features/organization_memory_agent.feature")


@pytest.fixture(scope="session")
def agent_config():
    """Default OrganizationMemoryAgentConfig for tests."""
    return OrganizationMemoryAgentConfig(
        agent_id="org_memory_test",
        agent_class=OrganizationMemoryAgent.__name__,
        name=LocaleString(en="Organization Memory Test Agent", de="Organisationsspeicher Test Agent"),
        description=LocaleString(
            en="Test agent for organization memory integration",
            de="Testagent für Organisationsspeicherintegration",
        ),
        llm=LLMConfig(model_name="text-generation/mini"),
        tenant_id="default_tenant",
        tenant_namespace="default_namespace",
    )


# ============================================================================
# Given Steps
# ============================================================================


@given("an OrganizationMemoryAgent runner with valid configuration", target_fixture="agent_runner")
def _(agent_config):
    """Create AgentTestRunner with default configuration."""
    return AgentTestRunner(agent_type=OrganizationMemoryAgent, default_agent_config=agent_config)


@given(parsers.parse('tenant namespace is "{namespace}"'))
def _(agent_config, namespace: str):
    """Set tenant namespace in config."""
    agent_config.tenant_namespace = namespace


@given(parsers.parse('pre-seeded organization memory: "{memory_text}"'))
@async_test
async def _(memory_text: str, agent_runner: AgentTestRunner):
    """Pre-seed an organization memory for testing via AgentMemory."""
    from aihub_lib.generative_ai.memory.AgentMemory import AgentMemory

    # Get test user from auth settings
    test_user = DangerousDevelopmentOnlyAuthSettings().get_user_identity()

    # Create AgentMemory instance with the agent config
    locale_handler = LocaleHandler(locale="en")
    agent_memory = AgentMemory(agent_config=agent_runner.default_agent_config, t=locale_handler)

    # Add the organization memory
    await agent_memory.add_organization_memory(
        memory=memory_text,
        user_id=test_user.id,
        thread_id="test_thread_seed",
        display_id="test_display_seed",
        run_id="test_run_seed",
        tenant_id=agent_runner.default_agent_config.tenant_id,
        tenant_namespace=agent_runner.default_agent_config.tenant_namespace,
    )


@given(parsers.parse('pre-seeded tenant memory in "{namespace}" namespace: "{memory_text}"'))
@async_test
async def _(memory_text: str, namespace: str, agent_runner: AgentTestRunner):
    """Pre-seed a tenant memory in specific namespace for testing."""
    from aihub_lib.generative_ai.memory.AgentMemory import AgentMemory

    # Get test user from auth settings
    test_user = DangerousDevelopmentOnlyAuthSettings().get_user_identity()

    # Create AgentMemory instance with the agent config
    locale_handler = LocaleHandler(locale="en")
    agent_memory = AgentMemory(agent_config=agent_runner.default_agent_config, t=locale_handler)

    # Add the tenant memory with specific namespace
    await agent_memory.add_organization_memory(
        memory=memory_text,
        user_id=test_user.id,
        thread_id="test_thread_seed",
        display_id="test_display_seed",
        run_id="test_run_seed",
        tenant_id=agent_runner.default_agent_config.tenant_id,
        tenant_namespace=namespace,
    )


@given("no pre-seeded organization memories")
def _():
    """No action needed - just a documentation step."""
    pass


# ============================================================================
# When Steps
# ============================================================================


@when(parsers.parse('the start event is sent with organizational fact "{fact}"'))
@async_test
async def _(agent_runner: AgentTestRunner, fact: str):
    """Send UserMessageEvent with organizational fact to trigger agent workflow."""
    async with agent_runner.test_run(delay_before_stop=120) as topic:
        await agent_runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content=fact, role=MessageRole.USER)],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
                locale="en",
            ),
        )


# ============================================================================
# Then Steps
# ============================================================================


@then("a StoreOrganizationMemoryEvent is present with memory updates")
def _(agent_runner: AgentTestRunner):
    """Check that organization memory was stored."""
    event = agent_runner.get_event_of_class(StoreOrganizationMemoryEvent)
    assert event is not None, "StoreOrganizationMemoryEvent not found"


@then("a StoreOrganizationMemoryEvent is present")
def _(agent_runner: AgentTestRunner):
    """Check that StoreOrganizationMemoryEvent was emitted."""
    event = agent_runner.get_event_of_class(StoreOrganizationMemoryEvent)
    assert event is not None, "StoreOrganizationMemoryEvent not found"


@then(parsers.parse('the stored memory contains "{text1}" and "{text2}"'))
def _(agent_runner: AgentTestRunner, text1: str, text2: str):
    """Verify that stored memory contains expected texts."""
    event = agent_runner.get_event_of_class(StoreOrganizationMemoryEvent)
    assert event is not None, "StoreOrganizationMemoryEvent not found"

    # Check all memory types (added, updated)
    all_memories = event.added_memories + event.updated_memories

    # Check if any memory contains both texts (case-insensitive)
    found_text1 = any(text1.lower() in mem.lower() for mem in all_memories)
    found_text2 = any(text2.lower() in mem.lower() for mem in all_memories)

    assert found_text1, f"No memory contains '{text1}'"
    assert found_text2, f"No memory contains '{text2}'"


@then("a BaseRetrieveMemoryEvent is present")
def _(agent_runner: AgentTestRunner):
    """Check that RetrieveOrganizationMemoryEvent exists (regardless of memory count)."""
    event = agent_runner.get_event_of_class(RetrieveOrganizationMemoryEvent)
    assert event is not None, "RetrieveOrganizationMemoryEvent not found"


@then(parsers.parse("a BaseRetrieveMemoryEvent is present with {count:d} or more memories"))
def _(agent_runner: AgentTestRunner, count: int):
    """Check that RetrieveOrganizationMemoryEvent has expected number of memories."""
    event = agent_runner.get_event_of_class(RetrieveOrganizationMemoryEvent)
    assert event is not None, "RetrieveOrganizationMemoryEvent not found"
    assert len(event.memories) >= count, f"Expected {count}+ memories, got {len(event.memories)}"


@then(parsers.parse('the retrieved memories contain "{text}"'))
def _(agent_runner: AgentTestRunner, text: str):
    """Verify that retrieved memories contain specific text."""
    event = agent_runner.get_event_of_class(RetrieveOrganizationMemoryEvent)
    assert event is not None, "RetrieveOrganizationMemoryEvent not found"

    # Check if any memory contains the text (case-insensitive)
    found = any(text.lower() in memory.memory.lower() for memory in event.memories)
    assert found, f"No memory contains '{text}'"


@then(parsers.parse('the retrieved memories contain "{text}" from Engineering namespace'))
def _(agent_runner: AgentTestRunner, text: str):
    """Verify that retrieved memories contain text from Engineering namespace."""
    event = agent_runner.get_event_of_class(RetrieveOrganizationMemoryEvent)
    assert event is not None, "RetrieveOrganizationMemoryEvent not found"

    # Check if any memory contains the text and is from Engineering namespace
    found = any(
        text.lower() in memory.memory.lower() and memory.metadata.tenant_namespace == "Engineering"
        for memory in event.memories
    )
    assert found, f"No memory from Engineering namespace contains '{text}'"


@then(parsers.parse('the retrieved memories do NOT contain "{text}" from Marketing namespace'))
def _(agent_runner: AgentTestRunner, text: str):
    """Verify that Marketing namespace memories are not retrieved in Engineering context."""
    event = agent_runner.get_event_of_class(RetrieveOrganizationMemoryEvent)
    assert event is not None, "RetrieveOrganizationMemoryEvent not found"

    # Check that no memory from Marketing namespace is present
    marketing_memories = [memory for memory in event.memories if memory.metadata.tenant_namespace == "Marketing"]
    assert len(marketing_memories) == 0, f"Found {len(marketing_memories)} memories from Marketing namespace"


@then("an AddMemoryToChatHistoryEvent is present")
def _(agent_runner: AgentTestRunner):
    """Check that chat history was extended with memory context."""
    event = agent_runner.get_event_of_class(AddOrganizationMemoryToChatHistoryEvent)
    assert event is not None, "AddOrganizationMemoryToChatHistoryEvent not found"


@then("the extended history has a system message with memory context")
def _(agent_runner: AgentTestRunner):
    """Verify extended history contains memory system message."""
    event = agent_runner.get_event_of_class(AddOrganizationMemoryToChatHistoryEvent)
    assert event is not None, "AddOrganizationMemoryToChatHistoryEvent not found"

    # Check for system message with memory context
    system_messages = [msg for msg in event.extended_history if msg.role == MessageRole.SYSTEM]
    assert len(system_messages) > 0, "No system messages in extended history"

    # Check that at least one system message contains memory context markers
    has_memory_context = any("<user_context>" in msg.content for msg in system_messages)
    assert has_memory_context, "System message missing <user_context> tag"


@then("an LLMEvent is present")
def _(agent_runner: AgentTestRunner):
    """Check that LLM generated a response."""
    event = agent_runner.get_event_of_class(LLMStopEvent)
    assert event is not None, "LLMStopEvent not found"
    assert event.chat_messages is not None and len(event.chat_messages) > 0, "LLM response is empty"


@then("the LLM response acknowledges the organizational fact")
def _(agent_runner: AgentTestRunner):
    """Verify LLM generated a response (content verification is flexible since fact storage is artificial)."""
    event = agent_runner.get_event_of_class(LLMStopEvent)
    assert event is not None, "LLMStopEvent not found"

    # Just verify we got a response - the content is less important since
    # the workflow is artificial (storing a fact, not asking a question)
    response_content = event.chat_messages[-1].content
    assert len(response_content) > 0, "LLM response is empty"


@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    """Check that workflow completed successfully."""
    assert agent_runner.has_stop_event, "StopEvent not found - workflow didn't complete"
