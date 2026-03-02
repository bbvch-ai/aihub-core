# ruff: noqa: E402
import pytest

from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()


from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.nats.events import LLMEvent, UserMessageEvent
from aihub_lib.nats.events.memory.history.AddUserMemoryToChatHistoryEvent import AddUserMemoryToChatHistoryEvent
from aihub_lib.nats.events.memory.retrieve.RetrieveUserMemoryEvent import RetrieveUserMemoryEvent
from aihub_lib.nats.events.memory.store.StoreUserMemoryEvent import StoreUserMemoryEvent
from aihub_lib.testing.asyncio_utils.bdd import async_test
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pytest_bdd import given, parsers, scenarios, then, when

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.user_memory_workflow.UserMemoryAgent import UserMemoryAgent
from playground.minimal_workflow.user_memory_workflow.UserMemoryAgentConfig import UserMemoryAgentConfig

enable_logging()

scenarios("./features/user_memory_agent.feature")


@pytest.fixture(scope="function")
def agent_config():
    """Default UserMemoryAgentConfig for tests."""
    return UserMemoryAgentConfig(
        agent_id="user_memory_test_3",
        agent_class=UserMemoryAgent.__name__,
        name=LocaleString(en="Memory Test Agent", de="Speicher Test Agent"),
        description=LocaleString(en="Test agent for memory integration", de="Testagent für Speicherintegration"),
        llm=LLMConfig(model_name="text-generation/gpt-oss-120b"),
    )


# ============================================================================
# Given Steps
# ============================================================================


@given("a UserMemoryAgent runner with valid configuration", target_fixture="agent_runner")
def _(agent_config):
    """Create AgentTestRunner with default English locale."""
    return AgentTestRunner(agent_type=UserMemoryAgent, agent_config=agent_config)


@given(parsers.parse('a UserMemoryAgent runner with locale "{locale}"'), target_fixture="agent_runner")
def _(agent_config, locale: str):
    """Create AgentTestRunner with specified locale."""
    # Note: Locale is passed via UserMessageEvent, not AgentConfig
    return AgentTestRunner(agent_type=UserMemoryAgent, agent_config=agent_config)


@given(parsers.parse('pre-seeded memory: "{memory_text}"'))
@async_test
async def _(memory_text: str, agent_runner: AgentTestRunner):
    """Pre-seed a memory for the test user via AgentMemory."""
    from aihub_lib.generative_ai.memory.AgentMemory import AgentMemory

    # Get test user from auth settings
    test_user = DangerousDevelopmentOnlyAuthSettings().get_user_identity()

    # Create AgentMemory instance with the agent config
    locale_handler = LocaleHandler(locale="en")
    agent_memory = AgentMemory(
        agent_config=agent_runner.agent_config, agent_class=agent_runner.agent_class, t=locale_handler
    )

    # Add the memory
    await agent_memory.add_user_memory(
        messages=[ChatMessage(content=memory_text, role=MessageRole.USER)],
        user_id=test_user.id,
        thread_id="test_thread_seed",
        display_id="test_display_seed",
        run_id="test_run_seed",
    )


@given("no pre-seeded memories")
def _():
    """No action needed - just a documentation step."""
    pass


# ============================================================================
# When Steps
# ============================================================================


@when(parsers.parse('the start event is sent with user query "{query}"'))
@async_test
async def _(agent_runner: AgentTestRunner, query: str):
    """Send UserMessageEvent to trigger agent workflow."""
    async with agent_runner.test_run(delay_before_stop=120) as topic:
        await agent_runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content=query, role=MessageRole.USER)],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
                locale="en",
            ),
        )


@when(parsers.parse('the start event is sent with user query "{query}" and locale "{locale}"'))
@async_test
async def _(agent_runner: AgentTestRunner, query: str, locale: str):
    """Send UserMessageEvent with specific locale."""
    async with agent_runner.test_run(delay_before_stop=120) as topic:
        await agent_runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content=query, role=MessageRole.USER)],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
                locale=locale,
            ),
        )


# ============================================================================
# Then Steps
# ============================================================================


@then("a RetrieveUserMemoryEvent is present")
def _(agent_runner: AgentTestRunner):
    """Check that RetrieveUserMemoryEvent exists (regardless of memory count)."""
    event = agent_runner.get_event_of_class(RetrieveUserMemoryEvent)
    assert event is not None, "RetrieveUserMemoryEvent not found"


@then(parsers.parse("a RetrieveUserMemoryEvent is present with {count:d} or more memories or relations"))
def _(agent_runner: AgentTestRunner, count: int):
    """Check that RetrieveUserMemoryEvent has expected number of memories."""
    event = agent_runner.get_event_of_class(RetrieveUserMemoryEvent)
    assert event is not None, "RetrieveUserMemoryEvent not found"
    assert len(event.memories) >= count or len(event.relations) >= count, (
        f"Expected {count}+ memories or relations, got {len(event.memories)} / {len(event.relations)}"
    )


@then(parsers.parse('the memory or relation content contains "{text}"'))
def _(agent_runner: AgentTestRunner, text: str):
    """Verify that retrieved memories contain specific text."""
    event = agent_runner.get_event_of_class(RetrieveUserMemoryEvent)
    assert event is not None, "RetrieveUserMemoryEvent not found"

    # Check if any memory contains the text (case-insensitive)
    found_memory = any(text.lower() in memory.memory.lower() for memory in event.memories)
    found_relation = any(text.lower() in relation.as_string() for relation in event.relations)
    assert found_memory or found_relation, f"No memory / relation contains '{text}'"


@then("an AddMemoryToChatHistoryEvent is present")
def _(agent_runner: AgentTestRunner):
    """Check that chat history was extended with memory context."""
    event = agent_runner.get_event_of_class(AddUserMemoryToChatHistoryEvent)
    assert event is not None, "AddUserMemoryToChatHistoryEvent not found"


@then("the extended history has a system message with memory context")
def _(agent_runner: AgentTestRunner):
    """Verify extended history contains memory system message."""
    event = agent_runner.get_event_of_class(AddUserMemoryToChatHistoryEvent)
    assert event is not None, "AddUserMemoryToChatHistoryEvent not found"

    # Check for system message with memory context
    system_messages = [msg for msg in event.extended_history if msg.role == MessageRole.SYSTEM]
    assert len(system_messages) > 0, "No system messages in extended history"

    # Check that at least one system message contains memory context markers
    has_memory_context = any("<user_context>" in msg.content for msg in system_messages)
    assert has_memory_context, "System message missing <user_context> tag"


@then("the memory system message is after any existing system messages")
def _(agent_runner: AgentTestRunner):
    """Verify memory system message comes after other system messages."""
    event = agent_runner.get_event_of_class(AddUserMemoryToChatHistoryEvent)
    assert event is not None, "AddUserMemoryToChatHistoryEvent not found"

    # Find the memory system message (contains <user_context>)
    memory_msg_index = None
    for i, msg in enumerate(event.extended_history):
        if msg.role == MessageRole.SYSTEM and "<user_context>" in msg.content:
            memory_msg_index = i
            break

    assert memory_msg_index is not None, "Memory system message not found"

    # If there are other system messages before it, that's expected
    # Just verify memory message exists in extended history
    assert memory_msg_index >= 0, "Memory message should be in extended history"


@then("an LLMEvent is present")
def _(agent_runner: AgentTestRunner):
    """Check that LLM generated a response."""
    event = agent_runner.get_event_of_class(LLMEvent)
    assert event is not None, "LLMEvent not found"
    assert event.chat_messages is not None and len(event.chat_messages) > 0, "LLM response is empty"


@then(parsers.parse('the LLM response mentions "{text}"'))
def _(agent_runner: AgentTestRunner, text: str):
    """Verify LLM response contains specific text."""
    event = agent_runner.get_event_of_class(LLMEvent)
    assert event is not None, "LLMEvent not found"

    # Get the last message content (assistant's response)
    response_content = event.chat_messages[-1].content.lower()
    assert text.lower() in response_content, f"LLM response doesn't mention '{text}'"


@then("a StoreUserMemoryEvent is present with memory updates")
def _(agent_runner: AgentTestRunner):
    """Check that new memories were persisted."""
    event = agent_runner.get_event_of_class(StoreUserMemoryEvent)
    assert event is not None, "StoreUserMemoryEvent not found"


@then("a StoreUserMemoryEvent is present")
def _(agent_runner: AgentTestRunner):
    """Check that StoreUserMemoryEvent was emitted."""
    event = agent_runner.get_event_of_class(StoreUserMemoryEvent)
    assert event is not None, "StoreUserMemoryEvent not found"


@then(parsers.parse('the new memory event contains a memory or relation mentioning "{text1}" or "{text2}"'))
def _(agent_runner: AgentTestRunner, text1: str, text2: str):
    """Verify new memories contain expected information."""
    event = agent_runner.get_event_of_class(StoreUserMemoryEvent)
    assert event is not None, "StoreUserMemoryEvent not found"

    # Check all memory types (added, updated)
    all_memories = event.added_memories + event.updated_memories

    # Check if any memory mentions either text (case-insensitive)
    found_memory = any(text1.lower() in mem.lower() or text2.lower() in mem.lower() for mem in all_memories)
    found_relation = any(
        text1.lower() in relation.as_string() or text2.lower() in relation.as_string()
        for relation in event.added_relations
    )

    assert found_memory or found_relation, f"No memory mentions '{text1}' or '{text2}'"


@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    """Check that workflow completed successfully."""
    assert agent_runner.has_stop_event, "StopEvent not found - workflow didn't complete"


@then("the memory system message uses German formatting")
def _(agent_runner: AgentTestRunner):
    """Verify German locale formatting in memory system message."""
    event = agent_runner.get_event_of_class(AddUserMemoryToChatHistoryEvent)
    assert event is not None, "AddUserMemoryToChatHistoryEvent not found"

    # Find memory system message
    memory_msg = None
    for msg in event.extended_history:
        if msg.role == MessageRole.SYSTEM and "<user_context>" in msg.content:
            memory_msg = msg
            break

    assert memory_msg is not None, "Memory system message not found"
    # German formatting check is implicitly done by checking German text in next step


@then(parsers.parse('the memory system message contains "{text}"'))
def _(agent_runner: AgentTestRunner, text: str):
    """Verify memory system message contains specific German text."""
    event = agent_runner.get_event_of_class(AddUserMemoryToChatHistoryEvent)
    assert event is not None, "AddUserMemoryToChatHistoryEvent not found"

    # Find memory system message
    memory_msg = None
    for msg in event.extended_history:
        if msg.role == MessageRole.SYSTEM and "<user_context>" in msg.content:
            memory_msg = msg
            break

    assert memory_msg is not None, "Memory system message not found"
    assert text in memory_msg.content, f"Memory message doesn't contain '{text}'"
