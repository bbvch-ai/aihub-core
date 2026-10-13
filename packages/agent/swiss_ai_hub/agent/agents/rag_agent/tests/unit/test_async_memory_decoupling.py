"""Unit tests for the delegation-event builder behind decoupled memory storage (issue #1179).

Delegation is the only storage mode — see ADR `2026_09_11_async_user_memory_storage_as_the_only_mode`. The
stop-gate itself is the spine's post-answer barrier, covered in `capabilities/tests`.
"""

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing.auth_utils import fake_user
from swiss_ai_hub.core.topics import AgentInstanceTopic

# Load rag_agent first: it has a module-level circular dependency with rag.preconditions/step_functions
# that only resolves in the runtime (rag_agent-first) order; importing preconditions first would break.
import swiss_ai_hub.agent.agents.rag_agent  # noqa: F401,E402  (import-order guard, not a direct dependency)
from swiss_ai_hub.agent.agents.rag_agent.configs.rag_agent_config import RAGAgentConfig
from swiss_ai_hub.agent.capabilities.memory.memory_step_functions import build_memory_storage_request
from swiss_ai_hub.agent.capabilities.memory.user_memory_config import UserMemoryConfig


def test_build_memory_storage_request_targets_writer_and_carries_origin():
    topic = AgentInstanceTopic(
        agent_class="RAGAgent",
        agent_id="hr",
        thread_id="t1",
        display_id="d1",
        run_id="r1",
        event_type="control_event",
        event_name="X",
        event_id="e1",
    )
    config = AgentConfig(agent_id="hr", name=LocaleString(en="HR"), description=LocaleString(en="HR agent"))
    event = build_memory_storage_request(
        user=fake_user(),
        messages=[ChatMessage(role=MessageRole.USER, content="hi")],
        topic=topic,
        agent_config=config,
        locale="en",
    )
    assert event.is_memory_storage_request_event
    assert (event.target_agent_class, event.target_agent_id) == ("MemoryWriterAgent", "memory-writer")
    assert event.start_event.origin_agent_class == "RAGAgent"
    assert event.start_event.origin_run_id == "r1"
    assert event.start_event.locale == "en"
    # A blueprint with no memory picker leaves the writer on the platform default.
    assert event.start_event.origin_memory_llm is None


def test_build_memory_storage_request_carries_the_origin_memory_model():
    """Issue #1590: a delegated write must extract on the same model an inline write would have used."""
    topic = AgentInstanceTopic(
        agent_class="RAGAgent",
        agent_id="hr",
        thread_id="t1",
        display_id="d1",
        run_id="r1",
        event_type="control_event",
        event_name="X",
        event_id="e1",
    )
    config = RAGAgentConfig(
        agent_id="hr",
        name=LocaleString(en="HR"),
        description=LocaleString(en="HR agent"),
        llm=LLMConfig(model_name="text-generation/main-model"),
        retrievers=[],
        user_memory=UserMemoryConfig(memory_llm="text-generation/memory-model"),
    )

    event = build_memory_storage_request(
        user=fake_user(),
        messages=[ChatMessage(role=MessageRole.USER, content="hi")],
        topic=topic,
        agent_config=config,
        locale="en",
    )

    assert event.start_event.origin_memory_llm == "text-generation/memory-model"
