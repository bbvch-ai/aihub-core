"""The permanent startup guard: the API refuses to start when a stored agent secret could not be masked.

Masking needs a usable key. A secret stored without one would surface only at runtime, where discovery drops the
profile it cannot build and the OpenWebUI sync deletes its model, so the guard must run before discovery starts.
"""

from typing import Any, Self
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from cryptography.fernet import Fernet
from fastapi import FastAPI
from mongoengine import connect, disconnect, signals
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.form import ALL_FORM_OPTIONS  # noqa: F401 — rebuilds Group
from swiss_ai_hub.core.imap import ImapClientConfig
from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.agents.agent_class_entity import AgentClassEntity
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity
from swiss_ai_hub.core.secrets import SecretEncryptionService

from swiss_ai_hub.api.runners.lifetime.lifetime_manager import lifetime_manager
from swiss_ai_hub.api.util.config_secrets import ConfigSecrets

_AGENT_CLASS = "KeyGuardMailboxAgent"
_KEY_VARIABLE = "AIHUB_CONFIG_ENCRYPTION_KEY"
_LIFETIME_MODULE = "swiss_ai_hub.api.runners.lifetime.lifetime_manager"


class _MailboxAgentConfig(AgentConfig):
    imap: ImapClientConfig

    @classmethod
    def as_form(cls) -> Self:
        base = AgentConfig.as_form()
        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            imap=ImapClientConfig.as_form(),
        )


@pytest.fixture
def mongo_connection():
    client = connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
    )
    yield client
    disconnect()


@pytest.fixture
def clean_configs(mongo_connection):
    with signals.post_save.muted(), signals.post_delete.muted():
        AgentConfigEntityDocument.objects.delete()
        AgentClassEntity.objects(agent_class=_AGENT_CLASS).delete()
        AgentClassEntity(
            agent_class=_AGENT_CLASS,
            form=[element.model_dump() for element in _MailboxAgentConfig.as_form().to_formkit_form()],
            is_conversational=False,
            start_events=[],
            stop_events=[],
            network_graph={},
        ).save(validate=False)
        yield
        AgentConfigEntityDocument.objects.delete()
        AgentClassEntity.objects(agent_class=_AGENT_CLASS).delete()


def _agent(password: Any) -> None:
    AgentConfigEntityDocument(
        agent_class=_AGENT_CLASS,
        agent_id="mailbox",
        name=LocaleStringEntity(en="mailbox"),
        description=LocaleStringEntity(en="mailbox profile"),
        icon="mage:robot",
        config_data={"imap": {"host": "imap.example.com", "password": password}},
    ).save()


@pytest.mark.usefixtures("clean_configs")
class TestEnsureKeyForStoredSecrets:
    def test_a_plaintext_secret_without_key_refuses(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv(_KEY_VARIABLE, raising=False)
        _agent("hunter2")

        with pytest.raises(ValueError, match=_KEY_VARIABLE):
            ConfigSecrets.ensure_key_for_stored_secrets()

    def test_ciphertext_without_key_refuses(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv(_KEY_VARIABLE, raising=False)
        _agent(SecretEncryptionService(Fernet.generate_key().decode()).encrypt("hunter2"))

        with pytest.raises(ValueError, match=_KEY_VARIABLE):
            ConfigSecrets.ensure_key_for_stored_secrets()

    def test_an_empty_key_refuses_naming_the_variable(self, monkeypatch: pytest.MonkeyPatch):
        """Compose hands an unset variable on as an empty string."""
        monkeypatch.setenv(_KEY_VARIABLE, "")
        _agent("hunter2")

        with pytest.raises(ValueError, match=_KEY_VARIABLE):
            ConfigSecrets.ensure_key_for_stored_secrets()

    def test_a_malformed_key_refuses(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv(_KEY_VARIABLE, "not-a-fernet-key")
        _agent("hunter2")

        with pytest.raises(ValueError):
            ConfigSecrets.ensure_key_for_stored_secrets()

    def test_blank_secrets_need_no_key(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv(_KEY_VARIABLE, raising=False)
        _agent("")

        ConfigSecrets.ensure_key_for_stored_secrets()

    def test_no_profiles_need_no_key(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv(_KEY_VARIABLE, raising=False)

        ConfigSecrets.ensure_key_for_stored_secrets()

    def test_a_usable_key_passes(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv(_KEY_VARIABLE, Fernet.generate_key().decode())
        _agent("hunter2")

        ConfigSecrets.ensure_key_for_stored_secrets()


@pytest.mark.asyncio
async def test_the_lifespan_runs_the_guard_before_the_config_responder_and_discovery():
    calls = MagicMock()
    refused = RuntimeError("key guard refused")
    calls.guard.side_effect = refused
    discovery = Mock()
    discovery.return_value.start = AsyncMock(side_effect=calls.discovery_start)
    responder = Mock()
    responder.return_value.start = AsyncMock(side_effect=calls.responder_start)

    with (
        patch(f"{_LIFETIME_MODULE}.connect"),
        patch(f"{_LIFETIME_MODULE}.ConfigSecrets.ensure_key_for_stored_secrets", calls.guard),
        patch(f"{_LIFETIME_MODULE}.AgentEndpointsDiscoveryService", discovery),
        patch(f"{_LIFETIME_MODULE}.AgentConfigResponder", responder),
        pytest.raises(RuntimeError) as raised,
    ):
        async with lifetime_manager(FastAPI()):
            pass

    assert raised.value is refused
    assert [name for name, _, _ in calls.mock_calls] == ["guard"]
