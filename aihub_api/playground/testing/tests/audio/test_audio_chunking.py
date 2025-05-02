import pytest
import io
from unittest.mock import Mock, AsyncMock
from fastapi import UploadFile, HTTPException
from pydub.generators import Sine
from pydub import AudioSegment

from aihub_api.audio.AudioChunkingService import AudioChunkingService


# Pre-generated audio cache
_AUDIO_CACHE = {}


def get_cached_audio(duration_ms: int, format: str = "wav") -> bytes:
    """Get audio from cache or generate and cache it."""
    cache_key = f"{duration_ms}_{format}"

    if cache_key not in _AUDIO_CACHE:
        # Generate audio only once
        sine_wave = Sine(440).to_audio_segment(duration=duration_ms)
        buffer = io.BytesIO()
        sine_wave.export(buffer, format=format)
        _AUDIO_CACHE[cache_key] = buffer.getvalue()

    return _AUDIO_CACHE[cache_key]


@pytest.fixture
def create_test_audio():
    """Creates test audio files with caching."""

    def _create_audio(duration_ms: int, format: str = "wav"):
        audio_bytes = get_cached_audio(duration_ms, format)
        buffer = io.BytesIO(audio_bytes)

        upload_file = UploadFile(filename=f"test_audio.{format}", file=buffer)
        upload_file.size = len(audio_bytes)
        return upload_file

    return _create_audio


@pytest.fixture
def mock_audio_segment():
    """Mock AudioSegment for faster testing."""

    def _mock_segment(duration_ms: int):
        mock = Mock(spec=AudioSegment)
        mock.__len__ = Mock(return_value=duration_ms)
        mock.frame_rate = 44100
        mock.channels = 2
        mock.sample_width = 2
        mock.export = Mock()
        return mock

    return _mock_segment


class TestAudioChunkingOptimized:

    @pytest.mark.asyncio
    async def test_small_file_no_chunking(self, create_test_audio):
        """Test that small files are not chunked - now faster."""
        # Use smaller duration for testing the same logic
        file = create_test_audio(10_000)  # 10 seconds instead of 30

        chunks = await AudioChunkingService.chunk_audio_file(file)

        assert len(chunks) == 1
        assert chunks[0][2]["chunk_index"] == 0
        assert chunks[0][2]["total_chunks"] == 1

    @pytest.mark.asyncio
    async def test_large_file_chunking_mocked(self, monkeypatch):
        """Test large file chunking with mocked AudioSegment for speed."""
        # Mock the audio loading and processing
        mock_audio = Mock(spec=AudioSegment)
        mock_audio.__len__ = Mock(return_value=15 * 60 * 1000)  # 15 minutes
        mock_audio.frame_rate = 44100
        mock_audio.channels = 2
        mock_audio.sample_width = 2

        # Mock export to create small files
        def mock_export(buffer, format):
            buffer.write(b"mock_audio_data")

        mock_audio.export = Mock(side_effect=mock_export)

        # Mock the slice operation for chunking
        def mock_getitem(slice_obj):
            chunk = Mock(spec=AudioSegment)
            if isinstance(slice_obj, slice):
                start = slice_obj.start or 0
                stop = slice_obj.stop or len(mock_audio)
                chunk.__len__ = Mock(return_value=stop - start)
            else:
                chunk.__len__ = Mock(return_value=1000)
            chunk.frame_rate = 44100
            chunk.channels = 2
            chunk.sample_width = 2
            chunk.export = Mock(side_effect=mock_export)
            return chunk

        mock_audio.__getitem__ = Mock(side_effect=mock_getitem)

        # Mock AudioSegment.from_file
        async def mock_validate_and_prepare(file):
            return mock_audio, "wav"

        monkeypatch.setattr(AudioChunkingService, "validate_and_prepare_audio", mock_validate_and_prepare)
        monkeypatch.setattr(AudioChunkingService, "find_silence_points", lambda x: [])

        file = Mock(spec=UploadFile)
        file.filename = "test.wav"
        file.size = 50 * 1024 * 1024  # 50 MB

        chunks = await AudioChunkingService.chunk_audio_file(file)

        assert len(chunks) > 1
        for i, (buffer, filename, metadata) in enumerate(chunks):
            assert metadata["chunk_index"] == i
            assert metadata["total_chunks"] == len(chunks)

    @pytest.mark.asyncio
    async def test_transcription_merging(self):
        """Test transcription merging without audio generation."""
        transcriptions = [
            ("This is the first part of the transcription", {"chunk_index": 0}),
            ("transcription and this is the second part", {"chunk_index": 1, "overlap_start": True}),
            ("part with some more text at the end", {"chunk_index": 2, "overlap_start": True}),
        ]

        merged = AudioChunkingService.merge_transcriptions(transcriptions)

        assert "transcription transcription" not in merged
        assert "part part" not in merged
        assert (
            "This is the first part of the transcription and this is the second part with some more text at the end"
            in merged
        )

    @pytest.mark.asyncio
    async def test_size_estimation(self, mock_audio_segment):
        """Test size estimation with mocked audio."""
        mock_audio = mock_audio_segment(10_000)  # 10 seconds

        estimated_size = AudioChunkingService.estimate_chunk_size(mock_audio)

        # Verify the calculation
        duration_seconds = 10.0
        expected_size = 44 + int(44100 * 2 * 2 * duration_seconds)
        assert estimated_size == expected_size

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling without actual file operations."""
        invalid_file = UploadFile(filename="invalid.txt", file=io.BytesIO(b"This is not an audio file"))

        with pytest.raises(HTTPException) as exc_info:
            await AudioChunkingService.chunk_audio_file(invalid_file)

        assert exc_info.value.status_code == 400
        assert "Invalid audio file" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_full_stt_with_chunking():
    """Fast integration test with all components mocked."""
    # Mock the heavy operations
    mock_chunks = [
        (io.BytesIO(b"chunk1"), "chunk_001.wav", {"chunk_index": 0}),
        (io.BytesIO(b"chunk2"), "chunk_002.wav", {"chunk_index": 1}),
        (io.BytesIO(b"chunk3"), "chunk_003.wav", {"chunk_index": 2}),
    ]

    # Mock AudioChunkingService
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(AudioChunkingService, "chunk_audio_file", AsyncMock(return_value=mock_chunks))

        # Create mock file
        mock_file = Mock(spec=UploadFile)
        mock_file.size = 100 * 1024 * 1024  # 100 MB
        mock_file.filename = "large_test.wav"

        # Mock OpenAI client
        mock_client = AsyncMock()
        mock_client.audio.transcriptions.create = AsyncMock(
            side_effect=[
                Mock(text="First chunk transcription"),
                Mock(text="Second chunk transcription"),
                Mock(text="Third chunk transcription"),
            ]
        )

        # Mock model config
        mock_model_config = Mock()
        mock_model_config.get_openai_client.return_value = mock_client
        mock_model_config.name = "test-model"

        # Test the service
        from aihub_api.routes.openai.OpenaiService import OpenaiService

        result = await OpenaiService.stt(
            stt_models=[mock_model_config],
            file=mock_file,
            model_name="test-model",
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
