"""The startup encryption of agent-config secrets stored in plaintext before #1587.

Every API replica runs it on every start, so it must encrypt exactly the plaintext at secret paths, leave ciphertext
and unannounced classes alone, lose to a save that lands between its read and its write, and need no key when there
is nothing to encrypt.
"""

from typing import Any, Self
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet
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

from swiss_ai_hub.api.runners.lifetime.plaintext_agent_secret_migration import PlaintextAgentSecretMigration

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
def mongo_connection():
    client = connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
    )
    yield client
    disconnect()


@pytest.fixture(autouse=True)
def clean_configs(mongo_connection):
    # Muted as in test_oversized_input_limit_migration: the change hook's receiver needs an event loop.
    with signals.post_save.muted(), signals.post_delete.muted():
        AgentConfigEntityDocument.objects.delete()
        AgentClassEntity.objects(agent_class=_AGENT_CLASS).delete()
        yield
        AgentConfigEntityDocument.objects.delete()
        AgentClassEntity.objects(agent_class=_AGENT_CLASS).delete()


@pytest.fixture
def encryption(monkeypatch: pytest.MonkeyPatch) -> SecretEncryptionService:
    key = Fernet.generate_key().decode()
    monkeypatch.setenv(_KEY_VARIABLE, key)
    return SecretEncryptionService(key)


def _announce() -> None:
    AgentClassEntity(
        agent_class=_AGENT_CLASS,
        form=[element.model_dump() for element in _MailboxAgentConfig.as_form().to_formkit_form()],
        is_conversational=False,
        start_events=[],
        stop_events=[],
        network_graph={},
    ).save(validate=False)


def _agent(agent_id: str, password: Any, **config: Any) -> AgentConfigEntityDocument:
    return AgentConfigEntityDocument(
        agent_class=_AGENT_CLASS,
        agent_id=agent_id,
        name=LocaleStringEntity(en=agent_id),
        description=LocaleStringEntity(en=f"{agent_id} profile"),
        icon="mage:robot",
        config_data={"imap": {"host": "imap.example.com", "password": password, "client_secret": ""}, **config},
    ).save()


def test_plaintext_is_encrypted(mongo_connection, encryption: SecretEncryptionService):
    _announce()
    agent = _agent("plain", "hunter2", inbox_folder="INBOX")

    assert PlaintextAgentSecretMigration.run() == [f"agent {_AGENT_CLASS}/plain"]

    config = agent.reload().config_data
    assert SecretEncryptionService.is_encrypted(config["imap"]["password"])
    assert encryption.decrypt(config["imap"]["password"]) == "hunter2"
    assert config["imap"]["client_secret"] == ""
    assert config["imap"]["host"] == "imap.example.com"
    assert config["inbox_folder"] == "INBOX"


def test_ciphertext_is_untouched_and_a_second_run_is_a_no_op(mongo_connection, encryption: SecretEncryptionService):
    _announce()
    ciphertext = encryption.encrypt("hunter2")
    agent = _agent("encrypted", ciphertext)

    assert PlaintextAgentSecretMigration.run() == []
    assert agent.reload().config_data["imap"]["password"] == ciphertext


def test_a_profile_whose_class_was_never_announced_is_left_alone(mongo_connection, encryption):
    agent = _agent("unannounced", "hunter2")

    assert PlaintextAgentSecretMigration.run() == []
    assert agent.reload().config_data["imap"]["password"] == "hunter2"


def test_a_save_between_read_and_write_wins(mongo_connection, encryption: SecretEncryptionService):
    _announce()
    stale = _agent("raced", "hunter2")
    newer = {"imap": {"host": "imap.example.com", "password": encryption.encrypt("changed"), "client_secret": ""}}
    AgentConfigEntityDocument.objects(pk=stale.pk).update_one(set__config_data=newer)

    with patch.object(AgentConfigEntityDocument, "find_all", return_value=[stale]):
        assert PlaintextAgentSecretMigration.run() == []

    assert stale.reload().config_data == newer


def test_formkit_dict_arrays_elsewhere_are_kept_as_they_are(mongo_connection, encryption: SecretEncryptionService):
    _announce()
    numbered = {"0": {"label": "a"}, "1": {"label": "b"}}
    agent = _agent("numbered", "hunter2", categories=numbered)

    assert PlaintextAgentSecretMigration.run() == [f"agent {_AGENT_CLASS}/numbered"]

    config = agent.reload().config_data
    assert config["categories"] == numbered
    assert encryption.decrypt(config["imap"]["password"]) == "hunter2"


def test_nothing_to_encrypt_builds_no_service(mongo_connection, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv(_KEY_VARIABLE, raising=False)
    _announce()
    _agent("blank", "")
    _agent("unset", None)

    with patch.object(SecretEncryptionService, "from_settings") as from_settings:
        assert PlaintextAgentSecretMigration.run() == []

    from_settings.assert_not_called()
