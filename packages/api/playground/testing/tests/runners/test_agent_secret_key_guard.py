"""The permanent startup guard: the API refuses to start when a stored agent secret could not be masked.

Masking needs a usable key. A secret stored without one would surface only at runtime, where discovery drops the
profile it cannot build and the OpenWebUI sync deletes its model, so the guard must run before discovery starts.
"""

from typing import Any, Self
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import pytest_asyncio
from cryptography.fernet import Fernet
from fastapi import FastAPI
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.form import ALL_FORM_OPTIONS  # noqa: F401 — rebuilds Group
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.imap import ImapClientConfig
from swiss_ai_hub.core.persistence.agents.agent_class_entity import AgentClassEntity
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument
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


@pytest_asyncio.fixture(loop_scope="session")
async def announced_class() -> None:
    # Class and profiles are Beanie documents, emptied before every test by `clean_beanie_collections`.
    await AgentClassEntity(
        agent_class=_AGENT_CLASS,
        form=[element.model_dump() for element in _MailboxAgentConfig.as_form().to_formkit_form()],
        is_conversational=False,
        start_events=[],
        stop_events=[],
        network_graph={},
    ).insert()


async def _agent(password: Any) -> None:
    await AgentConfigEntityDocument(
        agent_class=_AGENT_CLASS,
        agent_id="mailbox",
        name=LocaleString(en="mailbox"),
        description=LocaleString(en="mailbox profile"),
        icon="mage:robot",
        config_data={"imap": {"host": "imap.example.com", "password": password}},
    ).insert()


@pytest.mark.beanie
@pytest.mark.usefixtures("announced_class")
class TestEnsureKeyForStoredSecrets:
    async def test_a_plaintext_secret_without_key_refuses(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv(_KEY_VARIABLE, raising=False)
        await _agent("hunter2")

        with pytest.raises(ValueError, match=_KEY_VARIABLE):
            await ConfigSecrets.ensure_key_for_stored_secrets()

    async def test_ciphertext_without_key_refuses(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv(_KEY_VARIABLE, raising=False)
        await _agent(SecretEncryptionService(Fernet.generate_key().decode()).encrypt("hunter2"))

        with pytest.raises(ValueError, match=_KEY_VARIABLE):
            await ConfigSecrets.ensure_key_for_stored_secrets()

    async def test_an_empty_key_refuses_naming_the_variable(self, monkeypatch: pytest.MonkeyPatch):
        """Compose hands an unset variable on as an empty string."""
        monkeypatch.setenv(_KEY_VARIABLE, "")
        await _agent("hunter2")

        with pytest.raises(ValueError, match=_KEY_VARIABLE):
            await ConfigSecrets.ensure_key_for_stored_secrets()

    async def test_a_malformed_key_refuses(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv(_KEY_VARIABLE, "not-a-fernet-key")
        await _agent("hunter2")

        with pytest.raises(ValueError):
            await ConfigSecrets.ensure_key_for_stored_secrets()

    async def test_blank_secrets_need_no_key(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv(_KEY_VARIABLE, raising=False)
        await _agent("")

        await ConfigSecrets.ensure_key_for_stored_secrets()

    async def test_no_profiles_need_no_key(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv(_KEY_VARIABLE, raising=False)

        await ConfigSecrets.ensure_key_for_stored_secrets()

    async def test_a_usable_key_passes(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv(_KEY_VARIABLE, Fernet.generate_key().decode())
        await _agent("hunter2")

        await ConfigSecrets.ensure_key_for_stored_secrets()


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
