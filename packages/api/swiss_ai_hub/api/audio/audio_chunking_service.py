import logging
from typing import Annotated

from openai.types.audio import Transcription, TranscriptionVerbose
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

logger = logging.getLogger(__name__)

AudioChunk = Annotated[list[list[int]], "[[start: ms, end: ms]]"]
TranscriptionChunk = Transcription | TranscriptionVerbose | str


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

    # Conservative limits (20MB + 5MB buffer stays under OpenAI's 25MB limit)
    MAX_CHUNK_SIZE: Annotated[int, "bytes"] = 20 * 1024 * 1024
    MIN_SILENCE_LEN: Annotated[int, "ms"] = 500  # 500 ms is the typical minimum pause in natural speech
    SILENCE_THRESH: Annotated[
        int, "dB"
    ] = -40  # -40dB threshold identifies most speech pauses without excessive chunking

    @staticmethod
    def contains_speech(audio: AudioSegment) -> bool:
        """Whether the upload holds anything worth sending to the transcription gateway.

        OpenAI answers a silent upload with an empty transcript, but the gateway's WhisperX service
        raises instead — a recording the user never spoke into comes back as `Transcription failed: 0`,
        an HTTP 500 the caller can do nothing with. Verified against the provider on 2026-09-03 with
        silence, white noise and a pure tone.
        """
        return bool(
            detect_nonsilent(
                audio,
                min_silence_len=AudioChunkingService.MIN_SILENCE_LEN,
                silence_thresh=AudioChunkingService.SILENCE_THRESH,
                seek_step=10,
            )
        )

    @staticmethod
    async def chunk_audio(audio: AudioSegment) -> list[AudioSegment]:
        file_size: Annotated[int, "bytes"] = len(audio.raw_data)
        total_duration: Annotated[int, "ms"] = len(audio)
        max_duration: Annotated[int, "ms"] = int(total_duration / (file_size / AudioChunkingService.MAX_CHUNK_SIZE))

        if total_duration <= max_duration:
            return [audio]

        nonsilent_chunks: Annotated[list[list[int]], "[[start: ms, end: ms]]"] = detect_nonsilent(
            audio,
            min_silence_len=AudioChunkingService.MIN_SILENCE_LEN,
            silence_thresh=AudioChunkingService.SILENCE_THRESH,
            seek_step=10,  # 10 ms step for faster processing
        )
        segments: list[AudioSegment] = []
        segment: Annotated[list[list[int]], "[[start: ms, end: ms]]"] = []
        for chunk in nonsilent_chunks:
            _, chunk_end = chunk
            if segment:
                segment_start = segment[0][0]
                segment_end = segment[-1][-1]

                if chunk_end - segment_start > max_duration:
                    segments.append(audio[segment_start:segment_end])
                    if len(segment) > 1:
                        segment = segment[-1:]
                    else:
                        logger.warning(f"Chunk too large for overlap: {segment}")

            segment.append(chunk)
        if segment:
            segments.append(audio[segment[0][0] : segment[-1][1]])

        return segments

    @staticmethod
    def merge_transcriptions(transcription_chunks: list[TranscriptionChunk]) -> str:
        if isinstance(transcription_chunks[0], str):

            def get_text(x: str):
                return x

        else:

            def get_text(x: Transcription | TranscriptionVerbose):
                return x.text

        merged_words: list[str] = []
        for chunk in transcription_chunks:
            chunk_text = get_text(chunk)
            chunk_words = chunk_text.split()
            i = min(len(chunk_words), len(merged_words))
            while i > 0:
                if chunk_words[:i] == merged_words[-i:]:
                    break
                i -= 1
            merged_words.extend(chunk_words[i:])

        return " ".join(merged_words)
