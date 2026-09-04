import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import UploadFile
from openai.types.audio import TranscriptionVerbose
from pydub import AudioSegment
from pydub.generators import Sine
from swiss_ai_hub.core.auth import AccessChecker
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.api.audio.audio_chunking_service import AudioChunkingService
from swiss_ai_hub.api.routes.openai.openai_service import OpenaiService

_SERVICE = "swiss_ai_hub.api.routes.openai.openai_service"
_MODEL = "transcription/whisper-large-v3"


def _upload(audio: AudioSegment, filename: str = "recording.wav") -> UploadFile:
    buffer = io.BytesIO()
    audio.export(buffer, format="wav")
    return UploadFile(filename=filename, file=buffer, size=len(audio.raw_data))


def _spoken_audio() -> AudioSegment:
    return AudioSegment.silent(duration=500) + Sine(440).to_audio_segment(duration=3000)


async def _transcribe(file: UploadFile, mock_client: AsyncMock, **overrides):
    kwargs = {
        "model_name": _MODEL,
        "file": file,
        "user": fake_user(),
        "language": None,
        "prompt": None,
        "response_format": "json",
        "temperature": 0.0,
        "timestamp_granularities": None,
    } | overrides

    with (
        patch(f"{_SERVICE}.LiteLLMService.openai_aclient_for_user", return_value=mock_client),
        patch.object(OpenaiService, "_model_names_by_type", new=AsyncMock(return_value=[_MODEL])),
        patch(
            f"{_SERVICE}.AccessChecker.from_user",
            return_value=AccessChecker(["aihub.user.model.transcription.*"], tenant_access_rules=["aihub.admin.>"]),
        ),
    ):
        return await OpenaiService.stt(**kwargs)


def _client_returning(text: str) -> AsyncMock:
    client = AsyncMock()
    transcription = MagicMock()
    transcription.text = text
    client.audio.transcriptions.create = AsyncMock(return_value=transcription)
    return client


class TestSilentUploadsNeverReachTheGateway:
    """The provider raises `Transcription failed: 0` on an upload with no speech instead of
    returning an empty transcript, so a recording nobody spoke into must be answered locally."""

    def test_silence_is_not_speech(self):
        assert AudioChunkingService.contains_speech(AudioSegment.silent(duration=5000)) is False

    def test_sound_is_speech(self):
        assert AudioChunkingService.contains_speech(_spoken_audio()) is True

    @pytest.mark.asyncio
    async def test_silent_upload_returns_empty_transcript_without_calling_the_gateway(self):
        client = _client_returning("should never be reached")

        result = await _transcribe(_upload(AudioSegment.silent(duration=5000)), client)

        assert result.text == ""
        client.audio.transcriptions.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_silent_upload_honours_the_requested_response_format(self):
        client = _client_returning("should never be reached")

        result = await _transcribe(_upload(AudioSegment.silent(duration=5000)), client, response_format="text")

        assert result == ""
        client.audio.transcriptions.create.assert_not_called()


class TestWordTimestampsAreOnlyRequestedWhenTheyCanBeReturned:
    """`timestamp_granularities` only shapes a `verbose_json` response, and asking for it drives the
    provider's alignment stage — the one that fails outright for languages it ships no model for."""

    @pytest.mark.asyncio
    async def test_granularities_are_dropped_for_a_json_response(self):
        client = _client_returning("hello")

        await _transcribe(_upload(_spoken_audio()), client, timestamp_granularities=["word"])

        assert client.audio.transcriptions.create.await_args.kwargs["timestamp_granularities"] is None

    @pytest.mark.asyncio
    async def test_granularities_are_forwarded_for_a_verbose_response(self):
        client = _client_returning("hello")

        await _transcribe(
            _upload(_spoken_audio()), client, response_format="verbose_json", timestamp_granularities=["word"]
        )

        assert client.audio.transcriptions.create.await_args.kwargs["timestamp_granularities"] == ["word"]


class TestVerboseResponsesSurviveAnUnspecifiedLanguage:
    """`TranscriptionVerbose.language` is a required string, so echoing the caller's unset language
    made the whole request fail validation after the transcription had already been paid for."""

    @pytest.mark.asyncio
    async def test_verbose_json_without_a_language_is_returned(self):
        client = _client_returning("hello")

        result = await _transcribe(_upload(_spoken_audio()), client, response_format="verbose_json")

        assert isinstance(result, TranscriptionVerbose)
        assert result.language == ""
        assert result.text == "hello"
