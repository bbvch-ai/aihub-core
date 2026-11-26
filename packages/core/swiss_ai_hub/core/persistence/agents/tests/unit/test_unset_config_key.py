"""Stripping a config key a blueprint has retired from the profiles still carrying it.

Used by the API at startup for keys whose field no longer exists (the first being
`user_memory.enable_async_memory_storage`, see ADR `2026_09_11_async_user_memory_storage_as_the_only_mode`).
Correctness never depended on it — a config model ignores keys it does not declare — so what matters here is
that it touches nothing else: the sibling values an admin actually set must survive, and a second boot must
be a no-op rather than a write.
"""

import pytest

from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument

pytestmark = pytest.mark.beanie

RETIRED_KEY = "user_memory.enable_async_memory_storage"


async def _profile(agent_id: str, user_memory: dict) -> AgentConfigEntityDocument:
    return await AgentConfigEntityDocument(
        agent_class="RAGAgent",
        agent_id=agent_id,
        name=LocaleString(en=agent_id),
        description=LocaleString(en=f"{agent_id} profile"),
        icon="meteor-icons:robot",
        config_data={"user_memory": user_memory},
    ).insert()


async def _stored_config_data(profile: AgentConfigEntityDocument) -> dict:
    return (await AgentConfigEntityDocument.get(profile.id)).config_data


async def test_the_retired_key_is_stripped_and_its_siblings_survive():
    profile = await _profile("hr", {"enable_async_memory_storage": False, "enable_user_memory_storage": True})

    stripped = await AgentConfigEntityDocument.unset_config_key(RETIRED_KEY)

    assert stripped == 1
    user_memory = (await _stored_config_data(profile))["user_memory"]
    assert "enable_async_memory_storage" not in user_memory
    assert user_memory["enable_user_memory_storage"] is True


async def test_a_second_pass_changes_nothing():
    """The API runs this on every boot, so the steady state must be a query that matches nothing."""
    await _profile("hr", {"enable_async_memory_storage": True})
    await AgentConfigEntityDocument.unset_config_key(RETIRED_KEY)

    assert await AgentConfigEntityDocument.unset_config_key(RETIRED_KEY) == 0


async def test_profiles_without_the_key_are_left_alone():
    profile = await _profile("legal", {"enable_user_memory_storage": False})

    assert await AgentConfigEntityDocument.unset_config_key(RETIRED_KEY) == 0
    assert await _stored_config_data(profile) == {"user_memory": {"enable_user_memory_storage": False}}
