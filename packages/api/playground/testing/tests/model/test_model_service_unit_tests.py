from contextlib import contextmanager
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_user

from swiss_ai_hub.api.routes.model.model_service import ModelService

_MODEL_SERVICE = "swiss_ai_hub.api.routes.model.model_service"

# One representative model per capability, mirroring the LiteLLM config naming
# convention (``<capability>/<model>``) plus the distinct ``model_info.mode``.
_LITELLM_MODELS = [
    {"model_name": "text-generation/gpt-4.1", "model_info": {"mode": "chat"}},
    {"model_name": "embedding/bge-m3", "model_info": {"mode": "embedding"}},
    {"model_name": "reranker/bge", "model_info": {"mode": "rerank"}},
    {"model_name": "transcription/whisper-large-v3", "model_info": {"mode": "audio_transcription"}},
]


class _FakeAsyncClient:
    """Fakes the shared, never-closed client ``get_model_list`` drives."""

    async def get(self, url: str, headers: dict[str, str]) -> Mock:
        assert headers == {"Authorization": "Bearer sk-user"}
        return Mock(json=Mock(return_value={"data": _LITELLM_MODELS}))


@contextmanager
def _patched_backend(access_rules: list[str], *, is_sys_admin: bool = False):
    """Stubs the LiteLLM model listing and pins the AccessChecker to explicit rules.

    Patching ``AccessChecker.from_user`` avoids the DB round-trip it makes via
    ``RoleEntity.get_access_rules_for_roles`` and lets each test state the grant directly.
    """
    checker = AccessChecker(access_rules, tenant_access_rules=["aihub.admin.>"], is_sys_admin=is_sys_admin)

    with (
        patch(
            f"{_MODEL_SERVICE}.LiteLLMProxySettings",
            return_value=Mock(httpx_aclient=_FakeAsyncClient()),
        ),
        patch(
            f"{_MODEL_SERVICE}.LiteLLMService.authorization_header_for_user",
            new=AsyncMock(return_value={"Authorization": "Bearer sk-user"}),
        ),
        patch(f"{_MODEL_SERVICE}.AccessChecker.from_user", return_value=checker),
    ):
        yield


def _names(models) -> set[str]:
    return {model.model_name for model in models}


class TestModelServiceAccessFiltering:
    @pytest.mark.asyncio
    async def test_get_model_list_filters_to_granted_capability(self):
        with _patched_backend(["aihub.user.model.text-generation.*"]):
            models = await ModelService.get_model_list(fake_user())
        assert _names(models) == {"text-generation/gpt-4.1"}

    @pytest.mark.asyncio
    async def test_get_model_list_no_grant_returns_empty(self):
        with _patched_backend(["aihub.user.agent.>"]):
            models = await ModelService.get_model_list(fake_user())
        assert models == []

    @pytest.mark.asyncio
    async def test_get_model_list_sysadmin_sees_every_model(self):
        with _patched_backend([], is_sys_admin=True):
            models = await ModelService.get_model_list(fake_user(is_sys_admin=True))
        assert _names(models) == {model["model_name"] for model in _LITELLM_MODELS}

    @pytest.mark.asyncio
    async def test_multiple_capability_grants_are_combined(self):
        with _patched_backend(["aihub.user.model.embedding.*", "aihub.user.model.reranker.*"]):
            models = await ModelService.get_model_list(fake_user())
        assert _names(models) == {"embedding/bge-m3", "reranker/bge"}

    @pytest.mark.asyncio
    async def test_get_model_by_name_returns_granted_model(self):
        with _patched_backend(["aihub.user.model.text-generation.*"]):
            model = await ModelService.get_model_by_name(fake_user(), "text-generation/gpt-4.1")
        assert model.model_name == "text-generation/gpt-4.1"

    @pytest.mark.asyncio
    async def test_get_model_by_name_hidden_model_is_404(self):
        with _patched_backend(["aihub.user.model.text-generation.*"]):
            with pytest.raises(HTTPException) as exc:
                await ModelService.get_model_by_name(fake_user(), "embedding/bge-m3")
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_models_by_mode_inherits_capability_filter(self):
        with _patched_backend(["aihub.user.model.embedding.*"]):
            embedding_models = await ModelService.get_models_by_mode(fake_user(), "embedding")
            chat_models = await ModelService.get_models_by_mode(fake_user(), "chat")
        assert _names(embedding_models) == {"embedding/bge-m3"}
        assert chat_models == []

    @pytest.mark.asyncio
    async def test_get_grouped_model_list_only_groups_granted_models(self):
        with _patched_backend(["aihub.user.model.text-generation.*"]):
            groups = await ModelService.get_grouped_model_list(fake_user())
        assert {group.name for group in groups} == {"chat"}
        assert _names(groups[0].models) == {"text-generation/gpt-4.1"}
