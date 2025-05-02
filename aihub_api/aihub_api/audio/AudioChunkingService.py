# AudioChunkingService.py
import io
import logging
from typing import List, Tuple, Optional, Dict, Any
from fastapi import UploadFile, HTTPException
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import tempfile
import os

logger = logging.getLogger(__name__)


class AudioChunkingService:
    # Conservative limits to ensure we stay under OpenAI's limit
    MAX_CHUNK_SIZE = 24 * 1024 * 1024  # 24 MB (leaving 2MB buffer)
    TARGET_CHUNK_DURATION = 10 * 60 * 1000  # 10 minutes in milliseconds
    OVERLAP_DURATION = 5 * 1000  # 5 seconds overlap to avoid cutting words
    MIN_SILENCE_LEN = 500  # 500ms silence for splitting
    SILENCE_THRESH = -40  # dB threshold for silence detection

    @staticmethod
    async def validate_and_prepare_audio(file: UploadFile) -> Tuple[AudioSegment, str]:
        """
        Validates and loads the audio file, returning the AudioSegment and format.
        """
        # Read file content
        content = await file.read()
        await file.seek(0)  # Reset for potential reuse

        # Detect format from filename
        filename = file.filename or "audio"
        file_ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "wav"

        # Create temporary file to handle the audio
        with tempfile.NamedTemporaryFile(suffix=f".{file_ext}", delete=False) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # Load audio with pydub
            audio = AudioSegment.from_file(temp_file_path)
            return audio, file_ext
        except Exception as e:
            logger.error(f"Failed to load audio file: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid audio file: {str(e)}")
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    @staticmethod
    def find_silence_points(
        audio: AudioSegment, min_silence_len: int = None, silence_thresh: int = None
    ) -> List[Tuple[int, int]]:
        """
        Finds silence points in the audio for optimal splitting.
        """
        min_silence_len = min_silence_len or AudioChunkingService.MIN_SILENCE_LEN
        silence_thresh = silence_thresh or AudioChunkingService.SILENCE_THRESH

        # Detect non-silent chunks
        nonsilent_chunks = detect_nonsilent(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)

        # Calculate silence points (gaps between non-silent chunks)
        silence_points = []
        for i in range(len(nonsilent_chunks) - 1):
            end_of_sound = nonsilent_chunks[i][1]
            start_of_next_sound = nonsilent_chunks[i + 1][0]
            silence_middle = (end_of_sound + start_of_next_sound) // 2
            silence_points.append(silence_middle)

        return silence_points

    @staticmethod
    def estimate_chunk_size(audio_segment: AudioSegment) -> int:
        """
        Estimates the size of an audio segment when exported to WAV.
        """
        # WAV size calculation: header + (sample_rate * channels * bytes_per_sample * duration_in_seconds)
        duration_seconds = len(audio_segment) / 1000.0
        bytes_per_sample = audio_segment.sample_width
        size_estimate = 44 + int(
            audio_segment.frame_rate * audio_segment.channels * bytes_per_sample * duration_seconds
        )
        return size_estimate

    @staticmethod
    async def chunk_audio_file(
        file: UploadFile, max_size: int = None, target_duration: int = None, overlap: int = None
    ) -> List[Tuple[io.BytesIO, str, Dict[str, Any]]]:
        """
        Intelligently chunks an audio file based on size and silence detection.
        Returns a list of (file_buffer, filename, metadata) tuples.
        """
        max_size = max_size or AudioChunkingService.MAX_CHUNK_SIZE
        target_duration = target_duration or AudioChunkingService.TARGET_CHUNK_DURATION
        overlap = overlap or AudioChunkingService.OVERLAP_DURATION

        # Load and validate audio
        audio, format_ext = await AudioChunkingService.validate_and_prepare_audio(file)
        total_duration = len(audio)

        # Check if chunking is needed
        estimated_size = AudioChunkingService.estimate_chunk_size(audio)
        if estimated_size <= max_size:
            # No chunking needed
            buffer = io.BytesIO()
            audio.export(buffer, format="wav")
            buffer.seek(0)
            base_name = file.filename.rsplit(".", 1)[0] if file.filename else "audio"
            return [
                (
                    buffer,
                    f"{base_name}.wav",  # Always use .wav extension
                    {"start_time": 0, "end_time": total_duration, "chunk_index": 0, "total_chunks": 1},
                )
            ]

        # Find silence points for optimal splitting
        silence_points = AudioChunkingService.find_silence_points(audio)

        chunks = []
        current_start = 0
        chunk_index = 0

        while current_start < total_duration:
            # Calculate target end time
            target_end = min(current_start + target_duration, total_duration)

            # Find the best silence point near the target end time
            best_split_point = target_end
            if silence_points:
                # Find silence points within ±30 seconds of target
                candidates = [sp for sp in silence_points if abs(sp - target_end) < 30000]
                if candidates:
                    best_split_point = min(candidates, key=lambda x: abs(x - target_end))

            # Extract chunk with overlap
            chunk_start = max(0, current_start - (overlap if current_start > 0 else 0))
            chunk_end = min(total_duration, best_split_point + (overlap if best_split_point < total_duration else 0))

            chunk_audio = audio[chunk_start:chunk_end]

            # Verify chunk size
            chunk_size = AudioChunkingService.estimate_chunk_size(chunk_audio)
            if chunk_size > max_size:
                # Chunk is still too large, split it further
                logger.warning(f"Chunk {chunk_index} is still too large ({chunk_size} bytes), splitting further")
                # Reduce target duration and retry
                target_duration = int(target_duration * 0.7)
                continue

            # Export chunk
            buffer = io.BytesIO()
            chunk_audio.export(buffer, format="wav")
            buffer.seek(0)

            # Generate filename and metadata
            base_name = file.filename.rsplit(".", 1)[0] if file.filename else "audio"
            chunk_filename = f"{base_name}_chunk_{chunk_index:03d}.wav"  # Always use .wav extension
            metadata = {
                "start_time": current_start,
                "end_time": best_split_point,
                "actual_start": chunk_start,
                "actual_end": chunk_end,
                "chunk_index": chunk_index,
                "overlap_start": chunk_start < current_start,
                "overlap_end": chunk_end > best_split_point,
            }

            chunks.append((buffer, chunk_filename, metadata))

            # Move to next chunk
            current_start = best_split_point
            chunk_index += 1

        # Add total chunks to metadata
        for _, _, metadata in chunks:
            metadata["total_chunks"] = len(chunks)

        return chunks

    @staticmethod
    def merge_transcriptions(transcriptions: List[Tuple[str, Dict[str, Any]]], remove_overlap: bool = True) -> str:
        """
        Intelligently merges transcriptions, handling overlaps.
        transcriptions: List of (text, metadata) tuples
        """
        if not transcriptions:
            return ""

        if len(transcriptions) == 1:
            return transcriptions[0][0]

        merged_text = []

        for i, (text, metadata) in enumerate(transcriptions):
            if i == 0:
                # First chunk - use as is
                merged_text.append(text.strip())
            else:
                # Handle overlap with previous chunk
                if remove_overlap and metadata.get("overlap_start", False):
                    # Try to find where the overlap starts
                    prev_text = transcriptions[i - 1][0].strip()

                    # Simple approach: look for common words at boundaries
                    prev_words = prev_text.split()[-10:]  # Last 10 words of previous
                    curr_words = text.strip().split()[:10]  # First 10 words of current

                    # Find overlap point
                    overlap_start = 0
                    for j in range(min(len(prev_words), len(curr_words))):
                        if prev_words[-j - 1 :] == curr_words[: j + 1]:
                            overlap_start = j + 1

                    # Remove overlap from current text
                    if overlap_start > 0:
                        text_words = text.strip().split()
                        text = " ".join(text_words[overlap_start:])

                merged_text.append(text.strip())

        # Join all chunks with a space
        return " ".join(merged_text)
