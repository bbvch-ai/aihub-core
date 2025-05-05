import io
import logging
import os
import tempfile
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any, Annotated

from fastapi import UploadFile, HTTPException
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

logger = logging.getLogger(__name__)


@dataclass
class ChunkMetadata:
    """Metadata for an audio chunk enabling reassembly and transcription merging."""

    start_time: int
    end_time: int
    chunk_index: int
    total_chunks: int
    original_duration: int
    overlap_start: bool = False
    overlap_end: bool = False
    actual_start: Optional[int] = None
    actual_end: Optional[int] = None


@dataclass
class AudioChunk:
    """A single chunk of audio with its metadata and binary content."""

    buffer: io.BytesIO
    filename: str
    metadata: ChunkMetadata


@dataclass
class PreparedAudio:
    """Audio data with its format information."""

    audio: AudioSegment
    format: str


@dataclass
class TranscriptionChunk:
    """Transcribed text with its associated metadata."""

    text: str
    metadata: ChunkMetadata


class AudioChunkingService:
    """
    Service for intelligently chunking large audio files for processing by APIs with size limitations.

    Many speech-to-text APIs impose file size limits (like OpenAI's 25MB limit). Naively splitting
    audio can cut words mid-sentence and create poor transcription results. This service implements
    a sophisticated chunking algorithm that:

    1. Splits audio at silence points to preserve word boundaries and sentence integrity
    2. Adds overlaps between chunks to ensure continuity of speech
    3. Merges transcriptions intelligently by identifying and removing duplicated text at boundaries

    This approach allows processing files of any size while maintaining high transcription quality.
    """

    # Conservative limits (24MB + 1MB buffer stays under OpenAI's 25MB limit)
    MAX_CHUNK_SIZE = 24 * 1024 * 1024
    OVERLAP_DURATION = 5 * 1000  # 5-second overlap prevents losing context at boundaries
    MIN_SILENCE_LEN = 500  # 500 ms is the typical minimum pause in natural speech
    SILENCE_THRESH = -40  # -40dB threshold identifies most speech pauses without excessive chunking

    @staticmethod
    async def _validate_and_prepare_audio(file: UploadFile) -> PreparedAudio:
        """
        FastAPI provides files as streams, but pydub requires a file path.
        We need to save the file temporarily to allow pydub to process it.
        """
        content = await file.read()
        await file.seek(0)

        filename = file.filename or "audio"
        file_ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "wav"

        audio_bytes = io.BytesIO(content)
        try:
            audio = AudioSegment.from_file(audio_bytes, format=file_ext)
            return PreparedAudio(audio=audio, format=file_ext)
        except Exception as e:
            logger.error(f"Failed to load audio file: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid audio file: {str(e)}")

    @staticmethod
    def _find_silence_near_middle(
        audio: AudioSegment,
        start_ms: int,
        end_ms: int,
        min_silence_len: Optional[int] = None,
        silence_thresh: Optional[int] = None,
    ) -> Annotated[int, "ms"]:
        """
        Splitting audio at silence points preserves natural speech flow and
        prevents cutting words in half, which improves transcription quality.
        """
        min_silence_len = min_silence_len or AudioChunkingService.MIN_SILENCE_LEN
        silence_thresh = silence_thresh or AudioChunkingService.SILENCE_THRESH

        segment = audio[start_ms:end_ms]
        middle_point = (end_ms - start_ms) // 2

        nonsilent_chunks = detect_nonsilent(segment, min_silence_len=min_silence_len, silence_thresh=silence_thresh)

        if not nonsilent_chunks:
            return start_ms + middle_point

        silence_points = []
        for i in range(len(nonsilent_chunks) - 1):
            end_of_sound = nonsilent_chunks[i][1]
            start_of_next_sound = nonsilent_chunks[i + 1][0]
            silence_middle = (end_of_sound + start_of_next_sound) // 2
            silence_points.append(start_ms + silence_middle)

        if not silence_points:
            return start_ms + middle_point

        target_point = start_ms + middle_point
        return min(silence_points, key=lambda x: abs(x - target_point))

    @staticmethod
    def _estimate_chunk_size(audio_segment: AudioSegment) -> int:
        """
        We need to predict file size before exporting to avoid creating chunks
        that exceed API limits. This is more efficient than creating chunks
        and then checking their size afterward.
        """
        # WAV file format has a 44-byte header followed by PCM data
        WAV_HEADER_SIZE = 44

        duration_seconds = len(audio_segment) / 1000.0
        bytes_per_sample = audio_segment.sample_width

        size_estimate = WAV_HEADER_SIZE + int(
            audio_segment.frame_rate * audio_segment.channels * bytes_per_sample * duration_seconds
        )
        return size_estimate

    @staticmethod
    def _split_audio_recursively(
        audio: AudioSegment,
        start_ms: int,
        end_ms: int,
        max_size: int,
        overlap: int,
        base_name: str,
    ) -> List[AudioChunk]:
        """
        Binary recursive splitting is more efficient than linear segmentation for
        handling audio of unknown complexity. It adapts to audio content, creating
        larger chunks for simple audio and smaller chunks for complex audio.
        """
        segment = audio[start_ms:end_ms]
        estimated_size = AudioChunkingService._estimate_chunk_size(segment)

        if estimated_size <= max_size:
            buffer = io.BytesIO()
            segment.export(buffer, format="wav")
            buffer.seek(0)

            metadata = ChunkMetadata(
                start_time=start_ms,
                end_time=end_ms,
                chunk_index=0,  # Placeholder, updated later
                total_chunks=1,  # Placeholder, updated later
                original_duration=end_ms - start_ms,
            )

            return [
                AudioChunk(
                    buffer=buffer,
                    filename=f"{base_name}_chunk_000.wav",  # Placeholder, updated later
                    metadata=metadata,
                )
            ]

        split_point = AudioChunkingService._find_silence_near_middle(audio, start_ms, end_ms)

        if split_point <= start_ms or split_point >= end_ms:
            split_point = start_ms + (end_ms - start_ms) // 2

        left_chunks = AudioChunkingService._split_audio_recursively(
            audio, start_ms, split_point, max_size, overlap, base_name
        )

        right_chunks = AudioChunkingService._split_audio_recursively(
            audio, split_point, end_ms, max_size, overlap, base_name
        )

        return left_chunks + right_chunks

    @staticmethod
    async def chunk_audio_file(
        file: UploadFile, max_size: Optional[int] = None, overlap: Optional[int] = None
    ) -> List[AudioChunk]:
        max_size = max_size or AudioChunkingService.MAX_CHUNK_SIZE
        overlap = overlap or AudioChunkingService.OVERLAP_DURATION

        prepared_audio = await AudioChunkingService._validate_and_prepare_audio(file)
        audio = prepared_audio.audio
        total_duration = len(audio)

        estimated_size = AudioChunkingService._estimate_chunk_size(audio)
        if estimated_size <= max_size:
            buffer = io.BytesIO()
            audio.export(buffer, format="wav")
            buffer.seek(0)

            base_name = file.filename.rsplit(".", 1)[0] if file.filename else "audio"

            metadata = ChunkMetadata(
                start_time=0, end_time=total_duration, chunk_index=0, total_chunks=1, original_duration=total_duration
            )

            return [AudioChunk(buffer=buffer, filename=f"{base_name}.wav", metadata=metadata)]

        base_name = file.filename.rsplit(".", 1)[0] if file.filename else "audio"
        chunks = AudioChunkingService._split_audio_recursively(audio, 0, total_duration, max_size, overlap, base_name)

        chunks.sort(key=lambda chunk: chunk.metadata.start_time)

        for i, chunk in enumerate(chunks):
            chunk.metadata.chunk_index = i
            chunk.metadata.total_chunks = len(chunks)
            chunk.filename = f"{base_name}_chunk_{i:03d}.wav"

            if i > 0:
                chunk.metadata.overlap_start = True
            if i < len(chunks) - 1:
                chunk.metadata.overlap_end = True

        if overlap > 0:
            overlapped_chunks = []

            for i, chunk in enumerate(chunks):
                chunk_start = chunk.metadata.start_time
                chunk_end = chunk.metadata.end_time

                actual_start = max(0, chunk_start - (overlap if i > 0 else 0))
                actual_end = min(total_duration, chunk_end + (overlap if i < len(chunks) - 1 else 0))

                chunk_audio = audio[actual_start:actual_end]

                buffer = io.BytesIO()
                chunk_audio.export(buffer, format="wav")
                buffer.seek(0)

                chunk.metadata.actual_start = actual_start
                chunk.metadata.actual_end = actual_end

                chunk.buffer = buffer

                overlapped_chunks.append(chunk)

            chunks = overlapped_chunks

        return chunks

    @staticmethod
    def merge_transcriptions(transcription_chunks: List[TranscriptionChunk], remove_overlap: bool = True) -> str:
        """
        When transcribing overlapping chunks, duplicate text often appears at
        boundaries. This method detects repeated phrases and removes them to
        produce a clean, flowing transcription.
        """
        if not transcription_chunks:
            return ""

        if len(transcription_chunks) == 1:
            return transcription_chunks[0].text

        merged_text = []

        for i, chunk in enumerate(transcription_chunks):
            if i == 0:
                merged_text.append(chunk.text.strip())
            else:
                if remove_overlap and chunk.metadata.overlap_start:
                    prev_text = transcription_chunks[i - 1].text.strip()

                    prev_words = prev_text.split()[-10:]
                    curr_words = chunk.text.strip().split()[:10]

                    overlap_start = 0
                    for j in range(min(len(prev_words), len(curr_words))):
                        if prev_words[-j - 1 :] == curr_words[: j + 1]:
                            overlap_start = j + 1

                    if overlap_start > 0:
                        text_words = chunk.text.strip().split()
                        chunk_text = " ".join(text_words[overlap_start:])
                    else:
                        chunk_text = chunk.text.strip()
                else:
                    chunk_text = chunk.text.strip()

                merged_text.append(chunk_text)

        return " ".join(merged_text)
