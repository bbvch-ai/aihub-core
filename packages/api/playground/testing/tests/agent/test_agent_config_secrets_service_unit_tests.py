from contextlib import ExitStack
from datetime import datetime
from typing import Any, Self
from unittest.mock import AsyncMock, Mock, patch

import pytest
from cryptography.fernet import Fernet
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.form import ConfigSpecs
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.imap import ImapClientConfig
from swiss_ai_hub.core.persistence import AgentClassEntity
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity
from swiss_ai_hub.core.secrets import SecretEncryptionService

from swiss_ai_hub.api.routes.agent.agent_service import AgentService
from swiss_ai_hub.api.routes.agent.dto.create_agent_instance_request import CreateAgentInstanceRequest
from swiss_ai_hub.api.util.config_secrets import ConfigSecrets

_MODULE = "swiss_ai_hub.api.routes.agent.agent_service"
_KEY_VARIABLE = "AIHUB_CONFIG_ENCRYPTION_KEY"
_PASSWORD = "hunter2-mailbox-password"
_AGENT_CLASS = "MailboxAgent"


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


class _PlainAgentConfig(AgentConfig):
    pass


@pytest.fixture(autouse=True)
def online_threshold():
    with patch.object(AgentClassEntity, "online_threshold", return_value=datetime(2026, 1, 1)):
        yield


@pytest.fixture
def no_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(_KEY_VARIABLE, raising=False)


@pytest.fixture
def encryption(monkeypatch: pytest.MonkeyPatch) -> SecretEncryptionService:
    key = Fernet.generate_key().decode()
    monkeypatch.setenv(_KEY_VARIABLE, key)
    return SecretEncryptionService(key)


def _class_entity(config_type: type[AgentConfig] = _MailboxAgentConfig) -> Mock:
    form = config_type.as_form()
    class_entity = Mock()
    class_entity.agent_class = _AGENT_CLASS
    class_entity.is_online_since.return_value = True
    class_entity.is_conversational = False
    class_entity.is_schedulable = False
    class_entity.supports_response_schema = False
    class_entity.start_events = []
    class_entity.stop_events = []
    class_entity.hitl_request_events = []
    class_entity.hitl_response_events = []
    class_entity.network_graph = {"nodes": [], "links": []}
    class_entity.form = []
    class_entity.form_elements = form.to_formkit_form()
    class_entity.agent_config_specs.to_specs.return_value = ConfigSpecs.from_form(form, _AGENT_CLASS)
    class_entity.agent_config_specs.config_schema = ConfigSpecs.from_form(form, _AGENT_CLASS).config_schema
    return class_entity


def _config_entity(config_data: dict[str, Any]) -> Mock:
    config_entity = Mock()
    config_entity.agent_class = _AGENT_CLASS
    config_entity.agent_id = "mailbox"
    config_entity.name = LocaleStringEntity(en="Mailbox")
    config_entity.description = LocaleStringEntity(en="Reads a mailbox")
    config_entity.icon = "mage:robot"
    config_entity.config_data = config_data
    return config_entity


def _submission(password: str = _PASSWORD, **imap: Any) -> dict[str, Any]:
    return {
        "agent_id": "mailbox",
        "name": {"en": "Mailbox"},
        "description": {"en": "Reads a mailbox"},
        "icon": "mage:robot",
        "imap": {
            "host": "imap.example.com",
            "port": 993,
            "auth_method": "password",
            "username": "inbox@example.com",
            "password": password,
            "inbox_folder": "INBOX",
            "max_messages": 50,
            **imap,
        },
    }


def _patch_save_dependencies(stack: ExitStack, class_entity: Mock, stored: Mock | None) -> Mock:
    stack.enter_context(patch(f"{_MODULE}.AgentClassEntity.get_by_agent_class", return_value=class_entity))
    stack.enter_context(patch(f"{_MODULE}.AgentService._grant_instance_access"))
    stack.enter_context(
        patch(f"{_MODULE}.ModelLimitValidator.reject_values_beyond_model_limits", AsyncMock(return_value=None))
    )
    config_auth = stack.enter_context(patch(f"{_MODULE}.ConfigAuthorizationService"))
    config_auth.validate_for_user_or_raise = AsyncMock()
    config_doc = stack.enter_context(patch(f"{_MODULE}.AgentConfigEntityDocument"))
    config_doc.find_for_class_and_id.return_value = stored
    config_doc.side_effect = lambda **fields: _config_entity(fields["config_data"])
    return config_doc


async def _create(configuration: dict[str, Any], class_entity: Mock | None = None):
    request = CreateAgentInstanceRequest(agent_id="mailbox", configuration=configuration)
    user = Mock(acting_within_tenant=None)
    with ExitStack() as stack:
        config_doc = _patch_save_dependencies(stack, class_entity or _class_entity(), None)
        response = await AgentService.create_agent_instance(
            _AGENT_CLASS, request, LocaleHandler(locale="en"), user=user
        )
    return response, config_doc


async def _update(stored: Mock, configuration: dict[str, Any]) -> dict[str, Any]:
    with ExitStack() as stack:
        _patch_save_dependencies(stack, _class_entity(), stored)
        return await AgentService.update_agent_instance(
            _AGENT_CLASS, "mailbox", configuration, LocaleHandler(locale="en"), user=Mock()
        )


def _stored(encryption: SecretEncryptionService, password: str = _PASSWORD) -> Mock:
    config_data = {**_submission(password), "agent_class": _AGENT_CLASS}
    return _config_entity(encryption.encrypt_paths(config_data, {"imap.password"}))


def _mask_of(stored: Mock) -> str:
    return ConfigSecrets.masked(stored.config_data, _class_entity().form_elements)["imap"]["password"]


class TestCreate:
    @pytest.mark.asyncio
    async def test_encrypts_the_secret_and_answers_with_its_mask(self, encryption: SecretEncryptionService):
        response, config_doc = await _create(_submission())

        persisted = config_doc.call_args.kwargs["config_data"]["imap"]["password"]
        assert SecretEncryptionService.is_encrypted(persisted)
        assert encryption.decrypt(persisted) == _PASSWORD
        assert SecretEncryptionService.is_masked(response.configuration["imap"]["password"])
        assert _PASSWORD not in str(response.model_dump())
        assert persisted not in str(response.model_dump())

    @pytest.mark.asyncio
    async def test_a_mask_is_refused_with_400_not_500(self, encryption: SecretEncryptionService):
        mask = _mask_of(_stored(encryption))

        with pytest.raises(HTTPException) as raised:
            await _create(_submission(mask))

        assert raised.value.status_code == 400
        assert "imap.password" in raised.value.detail
        assert mask not in raised.value.detail

    @pytest.mark.asyncio
    async def test_a_class_without_secrets_needs_no_key(self, no_key: None):
        submission = {"agent_id": "plain", "name": {"en": "Plain"}, "description": {"en": "No secrets"}, "icon": "x"}

        response, config_doc = await _create(submission, _class_entity(_PlainAgentConfig))

        assert config_doc.call_args.kwargs["config_data"]["agent_id"] == "mailbox"
        assert response.configuration["name"] == {"en": "Plain"}

    @pytest.mark.asyncio
    async def test_blank_secrets_need_no_key(self, no_key: None):
        response, config_doc = await _create(_submission(""))

        assert config_doc.call_args.kwargs["config_data"]["imap"]["password"] == ""
        assert response.configuration["imap"]["password"] == ""

    @pytest.mark.asyncio
    async def test_a_secret_without_key_fails_naming_the_variable(self, no_key: None):
        with pytest.raises(ValueError, match=_KEY_VARIABLE):
            await _create(_submission())


class TestUpdate:
    @pytest.mark.asyncio
    async def test_the_unchanged_mask_keeps_the_stored_ciphertext(self, encryption: SecretEncryptionService):
        stored = _stored(encryption)
        ciphertext = stored.config_data["imap"]["password"]

        result = await _update(stored, _submission(_mask_of(stored)))

        assert stored.config_data["imap"]["password"] == ciphertext
        assert result["imap"]["password"] == ciphertext
        stored.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_a_new_secret_is_encrypted(self, encryption: SecretEncryptionService):
        stored = _stored(encryption)

        await _update(stored, _submission("a-brand-new-password"))

        persisted = stored.config_data["imap"]["password"]
        assert SecretEncryptionService.is_encrypted(persisted)
        assert encryption.decrypt(persisted) == "a-brand-new-password"

    @pytest.mark.asyncio
    async def test_re_saving_a_plaintext_profile_encrypts_it(self, encryption: SecretEncryptionService):
        stored = _config_entity({**_submission(), "agent_class": _AGENT_CLASS})

        await _update(stored, _submission(_mask_of(stored)))

        assert encryption.decrypt(stored.config_data["imap"]["password"]) == _PASSWORD

    @pytest.mark.asyncio
    @pytest.mark.parametrize("mask_kind", ["bare", "foreign"])
    async def test_a_mask_not_minted_from_this_profile_is_refused(
        self, encryption: SecretEncryptionService, mask_kind: str
    ):
        stored = _stored(encryption)
        mask = SecretEncryptionService.MASK if mask_kind == "bare" else _mask_of(_stored(encryption, "another"))

        with pytest.raises(HTTPException) as raised:
            await _update(stored, _submission(mask))

        assert raised.value.status_code == 400
        assert "imap.password" in raised.value.detail
        stored.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_submitted_ciphertext_is_refused_without_echoing_it(self, encryption: SecretEncryptionService):
        stored = _stored(encryption)
        replayed = encryption.encrypt("taken-from-elsewhere")

        with pytest.raises(HTTPException) as raised:
            await _update(stored, _submission(replayed))

        assert raised.value.status_code == 400
        assert replayed not in raised.value.detail
        stored.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_a_validation_400_does_not_echo_the_restored_ciphertext(self, encryption: SecretEncryptionService):
        stored = _stored(encryption)

        with pytest.raises(HTTPException) as raised:
            await _update(stored, _submission(_mask_of(stored), port="not-a-port"))

        assert raised.value.status_code == 400
        assert "'input'" not in raised.value.detail
        assert stored.config_data["imap"]["password"] not in raised.value.detail
        assert _PASSWORD not in raised.value.detail


class TestRestored:
    def test_a_none_submission_is_returned_as_it_is(self, no_key: None):
        assert ConfigSecrets.restored(None, {"imap": {"password": "x"}}, _class_entity().form_elements) is None

    def test_a_submission_without_secrets_needs_no_key(self, no_key: None):
        submission = _submission("")

        assert ConfigSecrets.restored(submission, None, _class_entity().form_elements) == submission


class TestRead:
    @pytest.mark.asyncio
    async def test_get_list_and_list_by_class_are_masked(self, encryption: SecretEncryptionService):
        stored = _stored(encryption)
        class_entity = _class_entity()
        t = LocaleHandler(locale="en")
        with (
            patch(f"{_MODULE}.AgentClassEntity.get_by_agent_class", return_value=class_entity),
            patch(f"{_MODULE}.AgentClassEntity.get_all", return_value=[class_entity]),
            patch(f"{_MODULE}.AgentConfigEntityDocument.find_for_class_and_id", return_value=stored),
            patch(f"{_MODULE}.AgentConfigEntityDocument.find_for_class", return_value=[stored]),
            patch(f"{_MODULE}.AgentConfigEntityDocument.find_for_name", return_value=[stored]),
        ):
            responses = [
                await AgentService.get_agent_instance(_AGENT_CLASS, "mailbox", t),
                *await AgentService.get_all_agent_instances(t),
                *await AgentService.get_agent_class_instances(_AGENT_CLASS, t),
            ]

        assert len(responses) == 3
        for response in responses:
            assert response.configuration["imap"]["password"] == _mask_of(stored)
            assert stored.config_data["imap"]["password"] not in str(response.model_dump())

    @pytest.mark.asyncio
    async def test_a_profile_with_blank_secrets_is_listed_without_a_key(self, no_key: None):
        stored = _config_entity({**_submission(""), "agent_class": _AGENT_CLASS})
        class_entity = _class_entity()
        with (
            patch(f"{_MODULE}.AgentClassEntity.get_all", return_value=[class_entity]),
            patch(f"{_MODULE}.AgentClassEntity.get_by_agent_class", return_value=class_entity),
            patch(f"{_MODULE}.AgentConfigEntityDocument.find_for_name", return_value=[stored]),
            patch(f"{_MODULE}.AgentConfigEntityDocument.find_for_class_and_id", return_value=stored),
        ):
            listed = await AgentService.get_all_agent_instances(LocaleHandler(locale="en"))
            single = await AgentService.get_agent_instance(_AGENT_CLASS, "mailbox", LocaleHandler(locale="en"))

        assert [instance.agent_id for instance in listed] == ["mailbox"]
        assert single.configuration["imap"]["password"] == ""

    @pytest.mark.asyncio
    async def test_a_stored_secret_without_key_answers_500(self, encryption: SecretEncryptionService, no_key: None):
        stored = _stored(encryption)
        app = FastAPI()

        @app.get("/instance")
        async def read_instance() -> dict[str, Any]:
            return (await AgentService.get_agent_instance(_AGENT_CLASS, "mailbox", LocaleHandler())).configuration

        with (
            patch(f"{_MODULE}.AgentClassEntity.get_by_agent_class", return_value=_class_entity()),
            patch(f"{_MODULE}.AgentConfigEntityDocument.find_for_class_and_id", return_value=stored),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test"
            ) as client:
                response = await client.get("/instance")

        assert response.status_code == 500
        assert stored.config_data["imap"]["password"] not in response.text
