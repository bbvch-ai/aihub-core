import io
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import UploadFile
from openai import InternalServerError
from openai.types.audio import TranscriptionVerbose
from pydub import AudioSegment
from pydub.generators import Sine
from swiss_ai_hub.core.auth import AccessChecker
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.api.audio.audio_chunking_service import AudioChunkingService
from swiss_ai_hub.api.routes.openai.openai_service import OpenaiService

_SERVICE = "swiss_ai_hub.api.routes.openai.openai_service"
_MODEL = "transcription/whisper-large-v3"

# Recorded verbatim from staging (api container, 2026-09-04T10:48:11Z) on a recording a user spoke
# into: the provider's alignment pass produced no segments and reports only their count.
NO_SEGMENTS_FAILURE = (
    "litellm.InternalServerError: InternalServerError: OpenAIException - Error code: 500 - "
    "{'detail': 'Transcription failed: Request b86b9b03-eba7-48e5-b5f6-ccd832bc6a0f failed: 500: "
    "Transcription failed: 0'}. Received Model Group=inference-whisper-large-v3\n"
    "Available Model Group Fallbacks=None LiteLLM Retried: 2 times, LiteLLM Max Retries: 2"
)
INVALID_MODEL_FAILURE = "litellm.InternalServerError: OpenAIException - Invalid model name passed in model=whisper-1"


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


def _client_failing_then_returning(failure: Exception, text: str) -> AsyncMock:
    client = AsyncMock()
    transcription = MagicMock()
    transcription.text = text
    client.audio.transcriptions.create = AsyncMock(side_effect=[failure, transcription])
    return client


def _upstream_failure(message: str) -> InternalServerError:
    body = {"error": {"message": message, "type": None, "param": None, "code": "500"}}
    request = httpx.Request("POST", "http://litellm:4000/audio/transcriptions")
    return InternalServerError("Error code: 500", response=httpx.Response(500, request=request, json=body), body=body)


def _two_chunks() -> list[AudioSegment]:
    return [Sine(440).to_audio_segment(duration=2000), Sine(440).to_audio_segment(duration=1500)]


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


class TestAudioTheProviderFindsNoSpeechIn:
    """`Transcription failed: 0` is the provider's verdict, not a fault: measured against it on
    2026-09-04, silence, a 440 Hz tone and white noise all come back with it, while 1.3 s of speech
    transcribes fine. So it means "no speech in this audio" — the same verdict `contains_speech`
    reaches locally for silence, and it gets the same answer: the transcript of whatever else was
    there, empty when that is nothing. It also repeats on every retry, so aborting the upload over
    one chunk threw away the chunks that did transcribe."""

    @pytest.mark.asyncio
    async def test_the_chunks_that_transcribed_are_still_returned(self):
        client = _client_failing_then_returning(_upstream_failure(NO_SEGMENTS_FAILURE), "the second half")

        with patch.object(AudioChunkingService, "chunk_audio", new=AsyncMock(return_value=_two_chunks())):
            result = await _transcribe(_upload(_spoken_audio()), client)

        assert result.text == "the second half"

    @pytest.mark.asyncio
    async def test_the_audio_left_out_is_logged_with_its_duration(self, caplog):
        """A transcript quietly missing a passage is worse than a failure, so how much audio is not
        in it has to be recoverable from the log."""
        client = _client_failing_then_returning(_upstream_failure(NO_SEGMENTS_FAILURE), "the second half")

        with (
            patch.object(AudioChunkingService, "chunk_audio", new=AsyncMock(return_value=_two_chunks())),
            caplog.at_level(logging.ERROR),
        ):
            await _transcribe(_upload(_spoken_audio()), client)

        assert "Chunk 1/2 (2000 ms) of recording.wav produced no transcript" in caplog.text
        assert "2000 ms of the 3500 ms in recording.wav is not in the transcript" in caplog.text
        # The provider's request id is the only handle for asking it about a chunk it rejected, so
        # the log keeps the upstream wording the response no longer carries.
        assert "b86b9b03-eba7-48e5-b5f6-ccd832bc6a0f" in caplog.text

    @pytest.mark.asyncio
    async def test_a_recording_with_no_speech_at_all_returns_an_empty_transcript(self, caplog):
        """This is the case staging hit: one chunk, no speech in it. Raising handed the chat user
        LiteLLM's nested traceback for a recording that simply had nothing to transcribe."""
        client = AsyncMock()
        client.audio.transcriptions.create = AsyncMock(side_effect=_upstream_failure(NO_SEGMENTS_FAILURE))

        with caplog.at_level(logging.ERROR):
            result = await _transcribe(_upload(_spoken_audio()), client)

        assert result.text == ""
        assert "3500 ms of the 3500 ms in recording.wav is not in the transcript" in caplog.text

    @pytest.mark.asyncio
    async def test_a_gateway_fault_is_not_answered_with_an_empty_transcript(self):
        """A misconfigured model or an expired key is not a verdict on the audio; answering it with
        an empty transcript would report "nobody spoke" for a deployment that transcribes nothing."""
        client = _client_failing_then_returning(_upstream_failure(INVALID_MODEL_FAILURE), "never reached")

        with patch.object(AudioChunkingService, "chunk_audio", new=AsyncMock(return_value=_two_chunks())):
            with pytest.raises(InternalServerError):
                await _transcribe(_upload(_spoken_audio()), client)
