"""Unit tests for decoupled memory storage wiring (issue #1179).

Covers the stop-gate precondition (`check_ready_for_stop`) across the three modes and the delegation-event
builder (`build_memory_storage_request`).
"""

from types import SimpleNamespace

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing.auth_utils import fake_user
from swiss_ai_hub.core.topics import AgentInstanceTopic

# Load rag_agent first: it has a module-level circular dependency with rag.preconditions/step_functions
# that only resolves in the runtime (rag_agent-first) order; importing preconditions first would break.
import swiss_ai_hub.agent.agents.rag_agent  # noqa: F401,E402  (import-order guard, not a direct dependency)
from swiss_ai_hub.agent.rag.preconditions import check_ready_for_stop
from swiss_ai_hub.agent.rag.step_functions import build_memory_storage_request

_STORE_EVENT = object()  # stand-in for a StoreUserMemoryEvent (check is identity/None only)
_MARKER = object()  # stand-in for a MemoryStorageRequestedEvent


def _config(storage_enabled: bool, async_enabled: bool) -> SimpleNamespace:
    return SimpleNamespace(
        user_memory=SimpleNamespace(
            enable_user_memory_storage=storage_enabled,
            enable_async_memory_storage=async_enabled,
        )
    )


def test_storage_disabled_never_gates():
    assert check_ready_for_stop(_config(storage_enabled=False, async_enabled=False), None, None) is True


def test_inline_mode_gates_on_store_event():
    config = _config(storage_enabled=True, async_enabled=False)
    assert check_ready_for_stop(config, None, None) is False
    assert check_ready_for_stop(config, _STORE_EVENT, None) is True
    # In inline mode the async marker must NOT satisfy the gate.
    assert check_ready_for_stop(config, None, _MARKER) is False


def test_async_mode_gates_on_marker_not_store_event():
    config = _config(storage_enabled=True, async_enabled=True)
    assert check_ready_for_stop(config, None, None) is False
    assert check_ready_for_stop(config, None, _MARKER) is True
    # In async mode the run must finalize on the cheap marker, not wait for a StoreUserMemoryEvent.
    assert check_ready_for_stop(config, _STORE_EVENT, None) is False


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
