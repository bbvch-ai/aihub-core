import pytest
import io
from fastapi import UploadFile, HTTPException
from pydub.generators import Sine
from pydub import AudioSegment

from aihub_api.audio.AudioChunkingService import AudioChunkingService


@pytest.fixture
def create_test_audio():
    """Creates test audio files of various sizes and formats."""

    def _create_audio(duration_ms: int, format: str = "wav"):
        # Generate a sine wave
        sine_wave = Sine(440).to_audio_segment(duration=duration_ms)

        # Export to buffer
        buffer = io.BytesIO()
        try:
            sine_wave.export(buffer, format=format)
        except FileNotFoundError:
            if format != "wav":
                # Fallback to WAV if ffmpeg is not available
                sine_wave.export(buffer, format="wav")
            else:
                raise

        # Get the size before seeking to start
        buffer.seek(0, io.SEEK_END)
        size = buffer.tell()
        buffer.seek(0)

        # Create UploadFile with size
        upload_file = UploadFile(filename=f"test_audio.{format}", file=buffer)
        upload_file.size = size  # Set the size attribute

        return upload_file

    return _create_audio


class TestAudioChunking:

    @pytest.mark.asyncio
    async def test_small_file_no_chunking(self, create_test_audio):
        """Test that small files are not chunked."""
        # Create a 30-second audio file
        file = create_test_audio(30_000)

        chunks = await AudioChunkingService.chunk_audio_file(file)

        assert len(chunks) == 1
        assert chunks[0][2]["chunk_index"] == 0
        assert chunks[0][2]["total_chunks"] == 1

    @pytest.mark.asyncio
    async def test_large_file_chunking(self, create_test_audio):
        """Test that large files are properly chunked."""
        # Create a 15-minute audio file
        file = create_test_audio(15 * 60 * 1000)

        chunks = await AudioChunkingService.chunk_audio_file(file)

        assert len(chunks) > 1

        # Verify chunk metadata
        for i, (buffer, filename, metadata) in enumerate(chunks):
            assert metadata["chunk_index"] == i
            assert metadata["total_chunks"] == len(chunks)
            assert "start_time" in metadata
            assert "end_time" in metadata

            # Verify no gaps between chunks
            if i > 0:
                prev_end = chunks[i - 1][2]["end_time"]
                curr_start = metadata["start_time"]
                assert curr_start == prev_end

    @pytest.mark.asyncio
    async def test_audio_continuity(self, create_test_audio):
        """Test that chunked audio maintains continuity."""
        # Create a test audio with distinct patterns
        duration = 5 * 60 * 1000  # 5 minutes
        target_duration = 2 * 60 * 1000  # 2 minutes per chunk

        # Create audio with alternating frequencies
        segment1 = Sine(440).to_audio_segment(duration=duration // 3)
        segment2 = Sine(880).to_audio_segment(duration=duration // 3)
        segment3 = Sine(440).to_audio_segment(duration=duration // 3)

        test_audio = segment1 + segment2 + segment3

        # Export to buffer
        buffer = io.BytesIO()
        test_audio.export(buffer, format="wav")
        buffer.seek(0)

        file = UploadFile(filename="test_pattern.wav", file=buffer)

        # Chunk the audio
        chunks = await AudioChunkingService.chunk_audio_file(file, target_duration=target_duration)

        # Verify we have multiple chunks
        assert len(chunks) > 1

        # Calculate expected total duration with overlaps
        expected_chunks = (duration + target_duration - 1) // target_duration

        # Each chunk (except first and last) adds one overlap
        expected_overlap = 0
        for i, (_, _, metadata) in enumerate(chunks):
            if metadata.get("overlap_start", False):
                expected_overlap += AudioChunkingService.OVERLAP_DURATION
            if metadata.get("overlap_end", False):
                expected_overlap += AudioChunkingService.OVERLAP_DURATION
        expected_total_duration = duration + expected_overlap

        # Reconstruct audio from chunks and verify total duration
        total_duration = 0
        for buffer, _, metadata in chunks:
            chunk_audio = AudioSegment.from_wav(buffer)
            total_duration += len(chunk_audio)

        # Allow for small differences due to rounding
        assert abs(total_duration - expected_total_duration) < 1000  # Less than 1 second difference

    @pytest.mark.asyncio
    async def test_audio_continuity_without_overlaps(self, create_test_audio):
        """Test that the logical audio segments (without overlaps) maintain continuity."""
        duration = 5 * 60 * 1000  # 5 minutes

        # Create test audio
        test_audio = Sine(440).to_audio_segment(duration=duration)

        buffer = io.BytesIO()
        test_audio.export(buffer, format="wav")
        buffer.seek(0)

        file = UploadFile(filename="test.wav", file=buffer)

        # Chunk the audio
        chunks = await AudioChunkingService.chunk_audio_file(file)

        # Check that the logical segments cover the entire duration
        total_logical_duration = 0
        last_end = 0

        for _, _, metadata in chunks:
            # Verify no gaps between logical segments
            assert metadata["start_time"] == last_end

            # Add logical duration (without overlap)
            total_logical_duration += metadata["end_time"] - metadata["start_time"]
            last_end = metadata["end_time"]

        # The logical segments should equal the original duration
        assert total_logical_duration == duration

    @pytest.mark.asyncio
    async def test_transcription_merging(self):
        """Test that transcriptions are properly merged."""
        transcriptions = [
            ("This is the first part of the transcription", {"chunk_index": 0}),
            ("transcription and this is the second part", {"chunk_index": 1, "overlap_start": True}),
            ("part with some more text at the end", {"chunk_index": 2, "overlap_start": True}),
        ]

        merged = AudioChunkingService.merge_transcriptions(transcriptions)

        # Should remove duplicate words at boundaries
        assert "transcription transcription" not in merged
        assert "part part" not in merged
        assert (
            "This is the first part of the transcription and this is the second part with some more text at the end"
            in merged
        )

    @pytest.mark.asyncio
    async def test_different_audio_formats(self, create_test_audio):
        """Test chunking with different audio formats."""
        formats = ["wav", "mp3", "ogg"]

        for format in formats:
            file = create_test_audio(2 * 60 * 1000, format=format)  # 2 minutes

            chunks = await AudioChunkingService.chunk_audio_file(file)

            assert len(chunks) >= 1

            # Verify all chunks are valid WAV files
            for buffer, filename, _ in chunks:
                assert filename.endswith(".wav")
                # Try to load the chunk to verify it's valid
                chunk_audio = AudioSegment.from_wav(buffer)
                assert len(chunk_audio) > 0

    @pytest.mark.asyncio
    async def test_size_estimation(self):
        """Test that size estimation is accurate."""
        # Create a known audio segment
        audio = Sine(440).to_audio_segment(duration=10_000)  # 10 seconds

        # Export to get actual size
        buffer = io.BytesIO()
        audio.export(buffer, format="wav")
        buffer.seek(0, io.SEEK_END)  # Seek to end to get size
        actual_size = buffer.tell()
        buffer.seek(0)  # Reset for potential reuse

        # Estimate size
        estimated_size = AudioChunkingService.estimate_chunk_size(audio)

        # Should be within 5% of actual size
        assert abs(estimated_size - actual_size) / actual_size < 0.05

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling for invalid files."""
        # Create an invalid file
        invalid_file = UploadFile(filename="invalid.txt", file=io.BytesIO(b"This is not an audio file"))

        with pytest.raises(HTTPException) as exc_info:
            await AudioChunkingService.chunk_audio_file(invalid_file)

        assert exc_info.value.status_code == 400
        assert "Invalid audio file" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_full_stt_with_chunking(create_test_audio):
    """Integration test for the full STT process with chunking."""
    from unittest.mock import AsyncMock, MagicMock

    # Create a large test file
    large_file = create_test_audio(20 * 60 * 1000)  # 20 minutes

    # Set file size for the mock UploadFile
    large_file.size = 100 * 1024 * 1024  # 100 MB (larger than limit)

    # Mock OpenAI client
    mock_client = AsyncMock()
    mock_client.audio.transcriptions.create = AsyncMock(
        side_effect=[
            MagicMock(text="First chunk transcription"),
            MagicMock(text="Second chunk transcription"),
            MagicMock(text="Third chunk transcription"),
        ]
    )

    # Mock the STT model config
    mock_model_config = MagicMock()
    mock_model_config.get_openai_client.return_value = mock_client
    mock_model_config.name = "test-model"

    # Test the service
    from aihub_api.routes.openai.OpenaiService import OpenaiService

    result = await OpenaiService.stt(
        stt_models=[mock_model_config],
        file=large_file,
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
