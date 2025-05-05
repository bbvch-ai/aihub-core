import tempfile
from typing import Annotated, List, Optional, Literal, Tuple, BinaryIO, IO

from fastapi import UploadFile
from openai import AsyncAzureOpenAI, AsyncOpenAI, NotGiven, NOT_GIVEN
from openai.types import FileContent, AudioModel
from openai.types.audio import Transcription, TranscriptionVerbose
from pydantic import BaseModel, Field
from pydub import AudioSegment


class AudioChunk(BaseModel):
    file_content: Annotated[BinaryIO, Field(...)]


TranscriptionChunk = Transcription | TranscriptionVerbose | str


class AudioTranscriptionService:
    """
    This service should be used to transcribe audio files with an OpenAI client.
    It ensures that large audio files are chunked into smaller pieces to avoid exceeding the file size limit.
    """

    OPENAI_AUDIO_MAX_FILE_SIZE: Annotated[int, "B"] = 25 * 1024 * 1024  # 25 MB
    WAV_FILE_TYPE: Annotated[str, "MIME"] = "audio/wav"

    @staticmethod
    async def transcribe_audio(
        file: UploadFile,
        client: AsyncOpenAI | AsyncAzureOpenAI,
        model_name: AudioModel | str = "whisper-1",
        language: str | NotGiven = NOT_GIVEN,
        prompt: str | NotGiven = NOT_GIVEN,
        response_format: str = "json",
        temperature: float = 0.0,
        timestamp_granularities: List[Literal["word", "segment"]] | NotGiven = NOT_GIVEN,
    ) -> Transcription | TranscriptionVerbose | str:
        with tempfile.TemporaryFile() as temp_file:
            await file.seek(0)
            temp_file.write(await file.read())
            temp_file.seek(0)
            audio_segment: AudioSegment = AudioSegment.from_file(temp_file)

        audio_chunks: List[AudioChunk] = AudioTranscriptionService._chunk_audio(file)
        transcription_chunks: List[TranscriptionChunk] = await AudioTranscriptionService._transcribe_chunks(
            file=file,
            audio_chunks=audio_chunks,
            client=client,
            model_name=model_name,
            language=language,
            prompt=prompt,
            response_format=response_format,
            temperature=temperature,
            timestamp_granularities=timestamp_granularities,
        )
        return AudioTranscriptionService._combine_transcriptions(transcription_chunks)

    @staticmethod
    def _chunk_audio(audio_segment: AudioSegment) -> List[AudioChunk]:
        if file.size <= AudioTranscriptionService.OPENAI_AUDIO_MAX_FILE_SIZE:
            return [AudioChunk(file_content=file.file)]
        else:
            pass  # TODO: Implement chunking logic

    @staticmethod
    async def _transcribe_chunks(
        file: UploadFile,
        audio_chunks: List["AudioChunk"],
        client: AsyncOpenAI | AsyncAzureOpenAI,
        model_name: AudioModel | str,
        language: str | NotGiven,
        prompt: str | NotGiven,
        response_format: str,
        temperature: float,
        timestamp_granularities: List[Literal["word", "segment"]] | NotGiven,
    ) -> List[TranscriptionChunk]:
        transcriptions: List[TranscriptionChunk] = []
        for chunk in audio_chunks:
            file_tuple: Tuple[Optional[str], IO[bytes], Optional[str]] = (
                file.filename,
                chunk.file_content,
                AudioTranscriptionService.WAV_FILE_TYPE,
            )
            transcription = await client.audio.transcriptions.create(
                file=file_tuple,
                model=model_name,
                language=language,
                prompt=prompt,
                response_format=response_format,
                temperature=temperature,
                timestamp_granularities=timestamp_granularities,
            )
            transcriptions.append(transcription)
        return transcriptions

    @staticmethod
    def _combine_transcriptions(
        transcription_chunks: List[TranscriptionChunk],
    ) -> Transcription | TranscriptionVerbose | str:
        pass  # TODO: Implement combining logic
