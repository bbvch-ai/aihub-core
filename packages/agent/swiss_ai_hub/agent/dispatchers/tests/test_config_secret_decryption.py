"""Agent-config secrets are decrypted at validation only (#1587).

The API serves a profile with its secrets encrypted, and the RPC reply, RunContext and Valkey keep it that way: only
the validated config of the event being handled holds plaintext, and an agent whose config holds no ciphertext needs no
key. That paths are computed lazily is pinned in `playground/minimal_workflow/configured_workflow/tests`.
"""

from collections.abc import AsyncIterator
from contextlib import ExitStack, asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from cryptography.fernet import Fernet
from swiss_ai_hub.core.events.agent import ExceptionEvent
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.imap import DraftEmailSettings, ImapClientConfig
from swiss_ai_hub.core.secrets import SecretEncryptionService
from swiss_ai_hub.core.testing import async_test

from swiss_ai_hub.agent.agents.email_classification_agent.configs.email_classification_agent_config import (
    EmailClassificationAgentConfig,
)
from swiss_ai_hub.agent.agents.imap_agent.configs.imap_agent_config import ImapAgentConfig
from swiss_ai_hub.agent.agents.imap_agent.events.read_mail_start_event import ReadMailStartEvent
from swiss_ai_hub.agent.agents.imap_agent.imap_agent import ImapAgent
from swiss_ai_hub.agent.agents.release_notes_agent.release_notes_agent_config import ReleaseNotesAgentConfig
from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.dispatchers.agent_dispatcher import AgentDispatcher
from swiss_ai_hub.agent.imap.tests.mail_doubles import infrastructure_patches, make_client
from swiss_ai_hub.agent.imap.tests.mail_doubles import summary as _summary
from swiss_ai_hub.agent.runners import AgentTestRunner

_KEY_VARIABLE = "AIHUB_CONFIG_ENCRYPTION_KEY"
_PASSWORD = "hunter2-mailbox-password"
_FACTORY = "swiss_ai_hub.agent.imap.imap_client.ImapClientFactory.create"


class _ServedConfigRunner(AgentTestRunner):
    """Serves the config the API would answer the RPC with, instead of the test config's own dump."""

    def __init__(self, served: dict[str, Any], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.served = served

    async def start(self) -> None:
        await super().start()
        self.dispatcher._config_client.fetch_config = AsyncMock(return_value=self.served)


def _imap_config() -> ImapAgentConfig:
    return ImapAgentConfig(
        agent_id="imap_agent",
        name=LocaleString(en="IMAP Agent"),
        description=LocaleString(en="Test agent"),
        imap=ImapClientConfig(host="imap.test", username="a@test", password=_PASSWORD),
        draft=DraftEmailSettings(
            enable_draft=False,
            source_folder="Processed",
            batch_size=5,
            drafts_folder="Drafts",
            model_name="text-generation/test-model",
        ),
    )


@pytest.fixture
def key(monkeypatch: pytest.MonkeyPatch) -> str:
    value = Fernet.generate_key().decode()
    monkeypatch.setenv(_KEY_VARIABLE, value)
    return value


@pytest.fixture
def no_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(_KEY_VARIABLE, raising=False)


def _encrypted_dump(key: str) -> dict[str, Any]:
    return SecretEncryptionService(key).encrypt_paths(_imap_config().model_dump(), {"imap.password"})


async def _read_mail(runner: AgentTestRunner) -> tuple[list[ImapClientConfig], list[Any]]:
    """Runs a mail read; returns every IMAP config a step opened a client with, and every stored run config."""
    opened: list[ImapClientConfig] = []
    stored: list[Any] = []
    client = make_client([_summary("1")], [], False)
    original_set = RunContext.set

    async def record_set(context: RunContext, key: str, value: Any, *args: Any, **kwargs: Any) -> Any:
        if key == AgentDispatcher._AGENT_CONFIG_KEY:
            stored.append(value)
        return await original_set(context, key, value, *args, **kwargs)

    @asynccontextmanager
    async def open_client(config: ImapClientConfig) -> AsyncIterator[AsyncMock]:
        opened.append(config)
        yield client

    with ExitStack() as stack:
        for patcher in infrastructure_patches(client):
            stack.enter_context(patcher)
        stack.enter_context(patch(_FACTORY, side_effect=open_client))
        stack.enter_context(patch.object(RunContext, "set", record_set))
        async with runner.test_run() as topic:
            await runner.send_event_from_topic(start_event=ReadMailStartEvent(), topic=topic)
    return opened, stored


@async_test
async def test_the_step_receives_plaintext_while_run_context_keeps_ciphertext(key: str):
    served = _encrypted_dump(key)
    runner = _ServedConfigRunner(served=served, agent_type=ImapAgent, agent_config=_imap_config())

    opened, stored = await _read_mail(runner)

    assert not runner.has_exception_event
    assert opened, "the read step never opened a client"
    assert {config.password for config in opened} == {_PASSWORD}
    assert stored, "the run config was never stored"
    for config in stored:
        assert config["imap"]["password"] == served["imap"]["password"]
        assert _PASSWORD not in str(config)


@async_test
async def test_ciphertext_outside_a_secret_path_stays_as_it_is(key: str):
    served = _encrypted_dump(key)
    username_ciphertext = SecretEncryptionService(key).encrypt("a@test")
    served["imap"]["username"] = username_ciphertext
    runner = _ServedConfigRunner(served=served, agent_type=ImapAgent, agent_config=_imap_config())

    opened, _ = await _read_mail(runner)

    assert not runner.has_exception_event
    assert {config.username for config in opened} == {username_ciphertext}
    assert {config.password for config in opened} == {_PASSWORD}


@async_test
async def test_ciphertext_without_a_key_ends_the_run_naming_the_variable(key: str, no_key: None):
    runner = _ServedConfigRunner(served=_encrypted_dump(key), agent_type=ImapAgent, agent_config=_imap_config())

    opened, _ = await _read_mail(runner)

    assert not opened
    exception = runner.get_event_of_class(ExceptionEvent)
    assert exception.message.startswith("The agent configuration is invalid:")
    assert _KEY_VARIABLE in exception.message


@async_test
async def test_plaintext_passes_through_without_a_key(no_key: None):
    runner = AgentTestRunner(agent_type=ImapAgent, agent_config=_imap_config())

    opened, _ = await _read_mail(runner)

    assert not runner.has_exception_event
    assert {config.password for config in opened} == {_PASSWORD}


@pytest.mark.parametrize(
    ("config_type", "paths"),
    [
        (ImapAgentConfig, {"imap.password", "imap.client_secret"}),
        (EmailClassificationAgentConfig, {"imap.password", "imap.client_secret"}),
        (ReleaseNotesAgentConfig, {"jira.api_token"}),
    ],
)
def test_secret_field_paths_are_read_off_the_class_form(config_type: type, paths: set[str]):
    assert config_type.secret_field_paths() == paths
