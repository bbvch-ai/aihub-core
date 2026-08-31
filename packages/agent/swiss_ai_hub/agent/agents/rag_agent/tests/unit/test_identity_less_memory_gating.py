"""`RAGStartEvent.user` is optional, so a RAG run can arrive with no identity at all.

A scheduled agent delegating to RAG forwards whatever its own start event carried, and a scheduled run carries
nothing — there is no service account to substitute. User memory is per-user by definition, so the only alternatives
are reading and writing nobody's memories (what these tests pin) or a shared identity's, which is how one mailbox's
context ends up in another customer's answer.

The subtle half is the three *downstream* gates. Skipping the memory steps is easy; skipping them without also
teaching the gates that wait on their events is how an identity-less run answers correctly and then never terminates.
"""

from types import SimpleNamespace

# Load rag_agent first: it has a module-level circular dependency with rag.preconditions that only resolves in the
# runtime (rag_agent-first) order; importing preconditions first would break. Same guard as
# `test_async_memory_decoupling`.
import swiss_ai_hub.agent.agents.rag_agent  # noqa: F401  (import-order guard, not a direct dependency)
from swiss_ai_hub.agent.rag.preconditions import (
    check_memory_added_to_chat_history,
    check_memory_ready_for_chat_history,
    check_ready_for_stop,
    check_user_memory_retrieval_enabled,
    check_user_memory_storage_enabled,
)


def _config(*, retrieval=True, storage=True, async_storage=False, org_memory=None) -> SimpleNamespace:
    return SimpleNamespace(
        user_memory=SimpleNamespace(
            enable_user_memory_retrieval=retrieval,
            enable_user_memory_storage=storage,
            enable_async_memory_storage=async_storage,
        ),
        org_memory=org_memory,
    )


def test_retrieval_is_skipped_without_an_identity_to_scope_it_to():
    assert check_user_memory_retrieval_enabled(_config(), has_user=True) is True
    assert check_user_memory_retrieval_enabled(_config(), has_user=False) is False


def test_storage_is_skipped_without_an_identity_to_attribute_it_to():
    assert check_user_memory_storage_enabled(_config(), has_user=True) is True
    assert check_user_memory_storage_enabled(_config(), has_user=False) is False


def test_the_config_switch_still_wins_when_there_is_an_identity():
    """The identity check narrows the config switch, it does not replace it."""
    assert check_user_memory_retrieval_enabled(_config(retrieval=False), has_user=True) is False
    assert check_user_memory_storage_enabled(_config(storage=False), has_user=True) is False


def test_chat_history_does_not_wait_for_a_memory_event_that_will_never_arrive():
    """The deadlock this prevents: the retrieval step is skipped, so its event never exists to wait for."""
    config = _config(org_memory=None)
    assert check_memory_ready_for_chat_history(config, True, None, None) is False, "with a user it waits"
    assert check_memory_ready_for_chat_history(config, False, None, None) is False, "with none there is nothing to do"


def test_organization_memory_still_runs_without_a_user():
    """Org memory is scoped to a tenant, which comes from the agent's own profile — not from the caller."""
    config = _config(retrieval=False, org_memory=SimpleNamespace())
    assert check_memory_ready_for_chat_history(config, False, None, None) is False, "it waits for the org event"
    assert check_memory_ready_for_chat_history(config, False, None, SimpleNamespace()) is True


def test_history_limiting_is_not_blocked_on_a_skipped_memory_step():
    assert check_memory_added_to_chat_history(_config(), True, None) is False
    assert check_memory_added_to_chat_history(_config(), False, None) is True


def test_the_run_still_terminates_when_the_memory_write_was_skipped():
    """The gate that would otherwise hang the run at its terminal step, having already produced the answer."""
    assert check_ready_for_stop(_config(), True, None, None) is False
    assert check_ready_for_stop(_config(), False, None, None) is True


def test_an_identity_less_run_terminates_in_async_storage_mode_too():
    config = _config(async_storage=True)
    assert check_ready_for_stop(config, True, None, None) is False
    assert check_ready_for_stop(config, False, None, None) is True
