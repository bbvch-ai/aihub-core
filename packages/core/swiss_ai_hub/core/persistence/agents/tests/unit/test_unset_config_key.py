"""Stripping a config key a blueprint has retired from the profiles still carrying it.

Used by the API at startup for keys whose field no longer exists (the first being
`user_memory.enable_async_memory_storage`, see ADR `2026_09_11_async_user_memory_storage_as_the_only_mode`).
Correctness never depended on it — a config model ignores keys it does not declare — so what matters here is
that it touches nothing else: the sibling values an admin actually set must survive, and a second boot must
be a no-op rather than a write.
"""

import pytest
from mongoengine import connect, disconnect

from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity

RETIRED_KEY = "user_memory__enable_async_memory_storage"


@pytest.fixture
def mongo_connection():
    client = connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
    )
    yield client
    disconnect()


@pytest.fixture(autouse=True)
def clean_configs(mongo_connection):
    AgentConfigEntityDocument.objects.delete()
    yield
    AgentConfigEntityDocument.objects.delete()


def _profile(agent_id: str, user_memory: dict) -> AgentConfigEntityDocument:
    return AgentConfigEntityDocument(
        agent_class="RAGAgent",
        agent_id=agent_id,
        name=LocaleStringEntity(en=agent_id),
        description=LocaleStringEntity(en=f"{agent_id} profile"),
        icon="meteor-icons:robot",
        config_data={"user_memory": user_memory},
    ).save()


def test_the_retired_key_is_stripped_and_its_siblings_survive(mongo_connection):
    profile = _profile("hr", {"enable_async_memory_storage": False, "enable_user_memory_storage": True})

    stripped = AgentConfigEntityDocument.unset_config_key(RETIRED_KEY)

    assert stripped == 1
    user_memory = profile.reload().config_data["user_memory"]
    assert "enable_async_memory_storage" not in user_memory
    assert user_memory["enable_user_memory_storage"] is True


def test_a_second_pass_changes_nothing(mongo_connection):
    """The API runs this on every boot, so the steady state must be a query that matches nothing."""
    _profile("hr", {"enable_async_memory_storage": True})
    AgentConfigEntityDocument.unset_config_key(RETIRED_KEY)

    assert AgentConfigEntityDocument.unset_config_key(RETIRED_KEY) == 0


def test_profiles_without_the_key_are_left_alone(mongo_connection):
    profile = _profile("legal", {"enable_user_memory_storage": False})

    assert AgentConfigEntityDocument.unset_config_key(RETIRED_KEY) == 0
    assert profile.reload().config_data == {"user_memory": {"enable_user_memory_storage": False}}
