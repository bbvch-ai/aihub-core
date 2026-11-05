"""The startup encryption of agent-config secrets stored in plaintext before #1587.

Every API replica runs it on every start, so it must encrypt exactly the plaintext at secret paths, leave ciphertext
and unannounced classes alone, lose to a save that lands between its read and its write, and need no key when there
is nothing to encrypt.
"""

from typing import Any, Self
from unittest.mock import AsyncMock, patch

import pytest
from cryptography.fernet import Fernet
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.form import ALL_FORM_OPTIONS  # noqa: F401 — rebuilds Group
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.imap import ImapClientConfig
from swiss_ai_hub.core.persistence.agents.agent_class_entity import AgentClassEntity
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument
from swiss_ai_hub.core.secrets import SecretEncryptionService

from swiss_ai_hub.api.runners.lifetime.plaintext_agent_secret_migration import PlaintextAgentSecretMigration

pytestmark = pytest.mark.beanie

_AGENT_CLASS = "SecretMigrationMailboxAgent"
_KEY_VARIABLE = "AIHUB_CONFIG_ENCRYPTION_KEY"


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
def encryption(monkeypatch: pytest.MonkeyPatch) -> SecretEncryptionService:
    key = Fernet.generate_key().decode()
    monkeypatch.setenv(_KEY_VARIABLE, key)
    return SecretEncryptionService(key)


async def _announce() -> None:
    # Class and profiles are Beanie documents, emptied before every test by `clean_beanie_collections`.
    await AgentClassEntity(
        agent_class=_AGENT_CLASS,
        form=[element.model_dump() for element in _MailboxAgentConfig.as_form().to_formkit_form()],
        is_conversational=False,
        start_events=[],
        stop_events=[],
        network_graph={},
    ).insert()


async def _agent(agent_id: str, password: Any, **config: Any) -> AgentConfigEntityDocument:
    return await AgentConfigEntityDocument(
        agent_class=_AGENT_CLASS,
        agent_id=agent_id,
        name=LocaleString(en=agent_id),
        description=LocaleString(en=f"{agent_id} profile"),
        icon="mage:robot",
        config_data={"imap": {"host": "imap.example.com", "password": password, "client_secret": ""}, **config},
    ).insert()


async def _stored_config(agent: AgentConfigEntityDocument) -> dict[str, Any]:
    return (await AgentConfigEntityDocument.get(agent.id)).config_data


async def test_plaintext_is_encrypted(encryption: SecretEncryptionService):
    await _announce()
    agent = await _agent("plain", "hunter2", inbox_folder="INBOX")

    assert await PlaintextAgentSecretMigration.run() == [f"agent {_AGENT_CLASS}/plain"]

    config = await _stored_config(agent)
    assert SecretEncryptionService.is_encrypted(config["imap"]["password"])
    assert encryption.decrypt(config["imap"]["password"]) == "hunter2"
    assert config["imap"]["client_secret"] == ""
    assert config["imap"]["host"] == "imap.example.com"
    assert config["inbox_folder"] == "INBOX"


async def test_ciphertext_is_untouched_and_a_second_run_is_a_no_op(encryption: SecretEncryptionService):
    await _announce()
    ciphertext = encryption.encrypt("hunter2")
    agent = await _agent("encrypted", ciphertext)

    assert await PlaintextAgentSecretMigration.run() == []
    assert (await _stored_config(agent))["imap"]["password"] == ciphertext


async def test_a_profile_whose_class_was_never_announced_is_left_alone(encryption):
    agent = await _agent("unannounced", "hunter2")

    assert await PlaintextAgentSecretMigration.run() == []
    assert (await _stored_config(agent))["imap"]["password"] == "hunter2"


async def test_a_save_between_read_and_write_wins(encryption: SecretEncryptionService):
    await _announce()
    stale = await _agent("raced", "hunter2")
    newer = {"imap": {"host": "imap.example.com", "password": encryption.encrypt("changed"), "client_secret": ""}}
    await AgentConfigEntityDocument.find({"_id": stale.id}).update({"$set": {"config_data": newer}})

    with patch.object(AgentConfigEntityDocument, "list_all", AsyncMock(return_value=[stale])):
        assert await PlaintextAgentSecretMigration.run() == []

    assert await _stored_config(stale) == newer


async def test_formkit_dict_arrays_elsewhere_are_kept_as_they_are(encryption: SecretEncryptionService):
    await _announce()
    numbered = {"0": {"label": "a"}, "1": {"label": "b"}}
    agent = await _agent("numbered", "hunter2", categories=numbered)

    assert await PlaintextAgentSecretMigration.run() == [f"agent {_AGENT_CLASS}/numbered"]

    config = await _stored_config(agent)
    assert config["categories"] == numbered
    assert encryption.decrypt(config["imap"]["password"]) == "hunter2"


async def test_nothing_to_encrypt_builds_no_service(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv(_KEY_VARIABLE, raising=False)
    await _announce()
    await _agent("blank", "")
    await _agent("unset", None)

    with patch.object(SecretEncryptionService, "from_settings") as from_settings:
        assert await PlaintextAgentSecretMigration.run() == []

    from_settings.assert_not_called()
