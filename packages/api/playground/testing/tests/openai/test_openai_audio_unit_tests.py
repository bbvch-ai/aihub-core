from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from swiss_ai_hub.core.auth import AccessChecker
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_user

from swiss_ai_hub.api.routes.openai.dto.text_to_speech_request import TextToSpeechRequest
from swiss_ai_hub.api.routes.openai.openai_service import OpenaiService

_SERVICE = "swiss_ai_hub.api.routes.openai.openai_service"

_TENANT_FULL = ["aihub.admin.>"]


def _checker(user_rules: list[str]) -> AccessChecker:
    return AccessChecker(user_rules, tenant_access_rules=_TENANT_FULL)


def _tts_request(model: str = "speech/some-tts") -> TextToSpeechRequest:
    return TextToSpeechRequest(model=model, input="hello", voice="alloy")


class TestModelInvocationReturns404ForUnknownModels:
    """A capability grant alone must satisfy the access check (no capability double-prefixing),
    and an unknown-but-granted model must surface as 404, never a bare ValueError (500)."""

    @pytest.mark.asyncio
    async def test_stt_unknown_model_is_404(self):
        with (
            patch(f"{_SERVICE}.AccessChecker.from_user", return_value=_checker(["aihub.user.model.transcription.*"])),
            patch.object(OpenaiService, "_model_names_by_type", new=AsyncMock(return_value=[])),
        ):
            with pytest.raises(HTTPException) as exc:
                await OpenaiService.stt(
                    model_name="transcription/does-not-exist",
                    file=Mock(),
                    user=fake_user(),
                    language=None,
                    prompt=None,
                    response_format="json",
                    temperature=0,
                    timestamp_granularities=None,
                )
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_tts_prefixed_grant_passes_access_and_unknown_model_is_404(self):
        with (
            patch(f"{_SERVICE}.AccessChecker.from_user", return_value=_checker(["aihub.user.model.speech.*"])),
            patch.object(OpenaiService, "_model_names_by_type", new=AsyncMock(return_value=[])),
        ):
            with pytest.raises(HTTPException) as exc:
                await OpenaiService.tts(
                    model_name="speech/some-tts",
                    input_text="hello",
                    tts_request=_tts_request(),
                    user=fake_user(),
                )
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_generate_image_unknown_model_is_404(self):
        generation_request = Mock()
        generation_request.model = "image-generation/does-not-exist"
        with (
            patch(
                f"{_SERVICE}.AccessChecker.from_user", return_value=_checker(["aihub.user.model.image-generation.*"])
            ),
            patch.object(OpenaiService, "_model_names_by_type", new=AsyncMock(return_value=[])),
        ):
            with pytest.raises(HTTPException) as exc:
                await OpenaiService.generate_image(
                    model_name="image-generation/does-not-exist",
                    image_generation_request=generation_request,
                    user=fake_user(),
                )
        assert exc.value.status_code == 404


class TestTtsAccessControl:
    @pytest.mark.asyncio
    async def test_tts_denies_without_access(self):
        with patch(f"{_SERVICE}.AccessChecker.from_user", return_value=_checker([])):
            with pytest.raises(HTTPException) as exc:
                await OpenaiService.tts(
                    model_name="speech/some-tts",
                    input_text="hello",
                    tts_request=_tts_request(),
                    user=fake_user(),
                )
        assert exc.value.status_code == 403


class TestTextToSpeechRequestModelField:
    def test_accepts_arbitrary_model_name(self):
        assert _tts_request(model="speech/kokoro").model == "speech/kokoro"

    def test_rejects_empty_model_name(self):
        with pytest.raises(ValidationError):
            _tts_request(model="")
