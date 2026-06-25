from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from swiss_ai_hub.core.auth import AccessChecker
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_user

from swiss_ai_hub.api.routes.openai.openai_controller import OpenaiController
from swiss_ai_hub.api.routes.openai.openai_service import OpenaiService

_CONTROLLER = "swiss_ai_hub.api.routes.openai.openai_controller"
_SERVICE = "swiss_ai_hub.api.routes.openai.openai_service"

# Tenant allows everything; the user's own rules are what each test varies.
_TENANT_FULL = ["aihub.admin.>"]


def _checker(user_rules: list[str]) -> AccessChecker:
    return AccessChecker(user_rules, tenant_access_rules=_TENANT_FULL)


class TestAssertModelAccessHelper:
    """Covers the shared guard used by embeddings / image / stt / tts."""

    def test_allows_granted_capability(self):
        with patch(
            f"{_CONTROLLER}.AccessChecker.from_user", return_value=_checker(["aihub.user.model.text-generation.*"])
        ):
            OpenaiController._assert_model_access(fake_user(), "text-generation/gemma-4-31B-it")  # no raise

    def test_denies_other_capability(self):
        with patch(
            f"{_CONTROLLER}.AccessChecker.from_user", return_value=_checker(["aihub.user.model.text-generation.*"])
        ):
            with pytest.raises(HTTPException) as exc:
                OpenaiController._assert_model_access(fake_user(), "embedding/bge-m3")
        assert exc.value.status_code == 403

    def test_denies_bare_name_without_capability(self):
        with patch(f"{_CONTROLLER}.AccessChecker.from_user", return_value=_checker(["aihub.user.model.>"])):
            with pytest.raises(HTTPException) as exc:
                OpenaiController._assert_model_access(fake_user(), "transcription")  # no slash -> empty name
        assert exc.value.status_code == 403


class TestChatCompletionModelAccess:
    @pytest.mark.asyncio
    async def test_denies_unpermitted_model(self):
        with (
            patch.object(OpenaiService, "get_model", new=AsyncMock()),  # model exists
            patch(f"{_SERVICE}.AccessChecker.from_user", return_value=_checker([])),  # user granted nothing
        ):
            with pytest.raises(HTTPException) as exc:
                await OpenaiService.chat_completion(
                    model_name="text-generation/gemma-4-31B-it",
                    chat_completion_request=Mock(),
                    user=fake_user(),
                    t=Mock(),
                )
        assert exc.value.status_code == 403
        assert "model" in exc.value.detail


class TestChatCompletionWithAssistantsBranching:
    async def _call_with_assistants(self, model_name: str):
        return await OpenaiService.chat_completion_with_assistants(
            model_name=model_name,
            chat_completion_request=Mock(),
            user=fake_user(),
            nc=Mock(),
            usage_limits=Mock(),
            external_agent_event_distributor=Mock(),
            t=Mock(),
        )

    @pytest.mark.asyncio
    async def test_denies_unpermitted_assistant(self):
        """Name is not a model (404) -> falls through to agent branch -> denied agent -> 403."""
        with (
            patch.object(
                OpenaiService,
                "chat_completion",
                new=AsyncMock(side_effect=HTTPException(status_code=404, detail="not found")),
            ),
            patch(f"{_SERVICE}.AccessChecker.from_user", return_value=_checker([])),
        ):
            with pytest.raises(HTTPException) as exc:
                await self._call_with_assistants("ResearchAgent/inst1")
        assert exc.value.status_code == 403
        assert "assistant" in exc.value.detail

    @pytest.mark.asyncio
    async def test_model_denial_propagates_and_is_not_masked_as_assistant(self):
        """A 403 from the model path must propagate, NOT be swallowed and retried as an agent."""
        with patch.object(
            OpenaiService,
            "chat_completion",
            new=AsyncMock(side_effect=HTTPException(status_code=403, detail="no access to model")),
        ):
            with pytest.raises(HTTPException) as exc:
                await self._call_with_assistants("text-generation/gemma-4-31B-it")
        assert exc.value.status_code == 403
        assert exc.value.detail == "no access to model"
