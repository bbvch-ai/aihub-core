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
    def find_silence_near_middle(
        audio: AudioSegment, start_ms: int, end_ms: int, min_silence_len: int = None, silence_thresh: int = None
    ) -> Optional[int]:
        """
        Finds a silence point near the middle of the specified audio segment.
        """
        min_silence_len = min_silence_len or AudioChunkingService.MIN_SILENCE_LEN
        silence_thresh = silence_thresh or AudioChunkingService.SILENCE_THRESH

        segment = audio[start_ms:end_ms]
        middle_point = (end_ms - start_ms) // 2

        # Detect non-silent chunks
        nonsilent_chunks = detect_nonsilent(segment, min_silence_len=min_silence_len, silence_thresh=silence_thresh)

        if not nonsilent_chunks:
            # The whole segment is silent
            return start_ms + middle_point

        # Find the silence point closest to the middle
        silence_points = []
        for i in range(len(nonsilent_chunks) - 1):
            end_of_sound = nonsilent_chunks[i][1]
            start_of_next_sound = nonsilent_chunks[i + 1][0]
            silence_middle = (end_of_sound + start_of_next_sound) // 2
            silence_points.append(start_ms + silence_middle)

        if not silence_points:
            # No silence found, fall back to middle point
            return start_ms + middle_point

        # Find silence point closest to the middle
        target_point = start_ms + middle_point
        return min(silence_points, key=lambda x: abs(x - target_point))

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
    def recursive_split(
        audio: AudioSegment,
        start_ms: int,
        end_ms: int,
        max_size: int,
        overlap: int,
        base_name: str,
        chunk_index_counter: List[int],  # Mutable list to track chunk indices
        results: List[Tuple[io.BytesIO, str, Dict[str, Any]]],
    ) -> None:
        """
        Recursively splits audio segments until they are within the size limit.
        """
        segment = audio[start_ms:end_ms]
        estimated_size = AudioChunkingService.estimate_chunk_size(segment)

        if estimated_size <= max_size:
            # This segment is small enough, add it to results
            chunk_index = chunk_index_counter[0]
            chunk_index_counter[0] += 1  # Increment counter

            # Export chunk
            buffer = io.BytesIO()
            segment.export(buffer, format="wav")
            buffer.seek(0)

            chunk_filename = f"{base_name}_chunk_{chunk_index:03d}.wav"
            metadata = {
                "start_time": start_ms,
                "end_time": end_ms,
                "chunk_index": chunk_index,
                "original_duration": end_ms - start_ms,
            }

            results.append((buffer, chunk_filename, metadata))
            return

        # Segment is too large, split it
        split_point = AudioChunkingService.find_silence_near_middle(audio, start_ms, end_ms)

        if split_point is None or split_point <= start_ms or split_point >= end_ms:
            # Can't split, force a middle split
            split_point = start_ms + (end_ms - start_ms) // 2

        # Recursively split left and right halves
        AudioChunkingService.recursive_split(
            audio, start_ms, split_point, max_size, overlap, base_name, chunk_index_counter, results
        )
        AudioChunkingService.recursive_split(
            audio, split_point, end_ms, max_size, overlap, base_name, chunk_index_counter, results
        )

    @staticmethod
    async def chunk_audio_file(
        file: UploadFile, max_size: int = None, overlap: int = None
    ) -> List[Tuple[io.BytesIO, str, Dict[str, Any]]]:
        """
        Intelligently chunks an audio file using recursive binary splitting.
        Returns a list of (file_buffer, filename, metadata) tuples.
        """
        max_size = max_size or AudioChunkingService.MAX_CHUNK_SIZE
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
                    f"{base_name}.wav",
                    {"start_time": 0, "end_time": total_duration, "chunk_index": 0, "total_chunks": 1},
                )
            ]

        # Use recursive splitting
        base_name = file.filename.rsplit(".", 1)[0] if file.filename else "audio"
        results = []
        chunk_index_counter = [0]  # Mutable counter for tracking chunk indices

        AudioChunkingService.recursive_split(
            audio, 0, total_duration, max_size, overlap, base_name, chunk_index_counter, results
        )

        # Sort results by chunk index to maintain order
        results.sort(key=lambda x: x[2]["chunk_index"])

        # Add total chunks to metadata and add overlap information
        for i, (buffer, filename, metadata) in enumerate(results):
            metadata["total_chunks"] = len(results)

            # Add overlap information for merging
            if i > 0:
                metadata["overlap_start"] = True
            if i < len(results) - 1:
                metadata["overlap_end"] = True

        # Apply overlaps if needed
        if overlap > 0:
            overlapped_results = []
            for i, (_, filename, metadata) in enumerate(results):
                chunk_start = metadata["start_time"]
                chunk_end = metadata["end_time"]

                # Apply overlap
                actual_start = max(0, chunk_start - (overlap if i > 0 else 0))
                actual_end = min(total_duration, chunk_end + (overlap if i < len(results) - 1 else 0))

                chunk_audio = audio[actual_start:actual_end]

                # Export chunk with overlap
                buffer = io.BytesIO()
                chunk_audio.export(buffer, format="wav")
                buffer.seek(0)

                # Update metadata with actual times
                metadata["actual_start"] = actual_start
                metadata["actual_end"] = actual_end

                overlapped_results.append((buffer, filename, metadata))

            results = overlapped_results

        return results

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
