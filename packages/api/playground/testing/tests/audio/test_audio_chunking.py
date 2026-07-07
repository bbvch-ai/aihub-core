import io

import pytest
from fastapi import UploadFile
from pydub import AudioSegment
from pydub.generators import Sine
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.api.audio.audio_chunking_service import AudioChunkingService


@pytest.fixture
def create_test_audio():
    """Creates test audio files of various sizes and formats."""

    def _create_audio(duration_ms: int, format: str = "wav"):
        silence = AudioSegment.silent(duration=1000)  # 1 second of silence
        sound = Sine(440).to_audio_segment(duration=4000)  # 4 seconds of sound
        pulse = silence + sound  # 1 second of silence + 4 seconds of sound

        pulse = pulse * (duration_ms // 5000)  # Repeat to fill the duration

        # Get the size before seeking to start
        size = len(pulse.raw_data)
        buffer = io.BytesIO()
        pulse.export(buffer, format=format)

        # Create UploadFile with size
        upload_file = UploadFile(filename=f"test_audio.{format}", file=buffer, size=size)

        return upload_file

    return _create_audio


class TestAudioChunking:
    @pytest.mark.asyncio
    async def test_small_file_no_chunking(self, create_test_audio):
        """Test that small files are not chunked."""
        # Create a 30-second audio file
        file = create_test_audio(30 * 1000)
        file_ext = file.filename.split(".")[-1].lower()
        audio = AudioSegment.from_file(file.file, format=file_ext)

        chunks = await AudioChunkingService.chunk_audio(audio)

        assert len(chunks) == 1

    @pytest.mark.asyncio
    async def test_large_file_chunking(self, create_test_audio):
        """Test that large files are properly chunked."""
        # Create a 10-minute audio file
        file = create_test_audio(10 * 60 * 1000)
        file_ext = file.filename.split(".")[-1].lower()
        audio = AudioSegment.from_file(file.file, format=file_ext)

        chunks = await AudioChunkingService.chunk_audio(audio)

        assert len(chunks) > 1

    @pytest.mark.asyncio
    async def test_transcription_merging(self):
        """Test transcription merging without audio generation."""
        transcriptions = [
            "This is the first part of the transcription",
            "transcription and this is the second part",
            "second part with some more text at the end",
        ]

        merged = AudioChunkingService.merge_transcriptions(transcriptions)

        assert (
            merged
            == "This is the first part of the transcription and this is the second part with some more text at the end"
        )

    @pytest.mark.asyncio
    async def test_different_audio_formats(self, create_test_audio):
        """Test chunking with different audio formats."""
        formats = ["wav", "mp3", "ogg"]

        for format in formats:
            file = create_test_audio(2 * 60 * 1000, format=format)  # 2 minutes
            file_ext = file.filename.split(".")[-1].lower()
            audio = AudioSegment.from_file(file.file, format=file_ext)

            chunks = await AudioChunkingService.chunk_audio(audio)

            assert len(chunks) >= 1

            # Verify all chunks are valid WAV files
            for chunk in chunks:
                # Try to load the chunk to verify it's valid
                buffer = io.BytesIO()
                chunk.export(buffer, format="wav")
                chunk_audio = AudioSegment.from_wav(buffer)
                assert len(chunk_audio) > 0


@pytest.mark.asyncio
async def test_full_stt_with_chunking(create_test_audio, monkeypatch):
    """Integration test for the full STT process with chunking."""
    from unittest.mock import AsyncMock, MagicMock, patch

    # Create a large test file
    large_file = create_test_audio(10 * 60 * 1000)  # 20 minutes

    # Mock OpenAI client
    mock_client = AsyncMock()
    mock_transcription_1 = MagicMock()
    mock_transcription_1.text = "First chunk transcription"
    mock_transcription_2 = MagicMock()
    mock_transcription_2.text = "Second chunk transcription"
    mock_transcription_3 = MagicMock()
    mock_transcription_3.text = "Third chunk transcription"

    mock_client.audio.transcriptions.create = AsyncMock(
        side_effect=[
            mock_transcription_1,
            mock_transcription_2,
            mock_transcription_3,
        ]
    )

    # Mock the model names by type
    async def mock_model_names(*args, **kwargs):
        return ["transcription/whisper-large-v3"]

    # Test the service
    from swiss_ai_hub.api.routes.openai.openai_service import OpenaiService

    with patch(
        "swiss_ai_hub.api.routes.openai.openai_service.LiteLLMService.openai_aclient_for_user"
    ) as mock_litellm_client:
        mock_litellm_client.return_value = mock_client

        with (
            patch.object(OpenaiService, "_model_names_by_type", side_effect=mock_model_names),
            patch.object(OpenaiService, "_assert_model_access"),
        ):
            result = await OpenaiService.stt(
                file=large_file,
                user=fake_user(),
                model_name="transcription/whisper-large-v3",
                language="en",
                prompt=None,
                response_format="json",
                temperature=0.0,
                timestamp_granularities=None,
            )

    # Verify the result
    assert hasattr(result, "text")
    assert "First chunk transcription" in result.text
    assert "Second chunk transcription" in result.text
    assert "Third chunk transcription" in result.text
