import asyncio
import hashlib
import logging
from collections.abc import Sequence
from typing import Annotated

from swiss_ai_hub.core.events.agent import AttachedFileEvent, AttachedFileStatus, UserUploadedFile
from swiss_ai_hub.core.generative_ai import CitationId, DocumentExtractor, ModelTokenBudget

from swiss_ai_hub.agent.capabilities.attached_files.attached_file_record import AttachedFileRecord
from swiss_ai_hub.agent.capabilities.attached_files.attached_file_section_cache import AttachedFileSectionCache
from swiss_ai_hub.agent.capabilities.attached_files.attached_file_sections import AttachedFileSections
from swiss_ai_hub.agent.capabilities.attached_files.attached_file_text import AttachedFileText

logger = logging.getLogger(__name__)

# MinerU serves MINERU_API_MAX_CONCURRENT_REQUESTS (3) conversions at once and answers the rest with 503. Reading a
# turn's attachments all at once sent a dozen PDFs into it together, and they ran out of their ~35s retry budget side
# by side. Two at a time leaves a slot for ingestion and other chats.
MAX_CONCURRENT_READS = 2


class AttachedFileReader:
    """Reads one attached file out of the agent's upload bucket into sections, reporting a file that cannot be read.

    A failure is an outcome, not an exception: the user asked about the file, so an unreadable one must end in an
    answer that says so, and one bad file must not take the other attachments of the turn down with it. A file read
    before comes from the section cache, without downloading or parsing it again.
    """

    @staticmethod
    def is_readable_attachment(file: UserUploadedFile) -> bool:
        """Images already reach the model as image content in the message, so they are not read as documents."""
        return not file.file_type.startswith("image/")

    @staticmethod
    async def read_all(
        files: Sequence[UserUploadedFile],
        agent_class: str,
        agent_id: str,
        embedding_budget: Annotated[ModelTokenBudget, "Of the embedding model that ranks the sections"],
        cache: AttachedFileSectionCache | None = None,
    ) -> list[tuple[AttachedFileText | None, AttachedFileEvent]]:
        """The files in the order given, read a few at a time so a turn with many attachments cannot flood MinerU."""
        slots = asyncio.Semaphore(MAX_CONCURRENT_READS)
        section_cache = cache or AttachedFileSectionCache()

        async def read_one(file: UserUploadedFile) -> tuple[AttachedFileText | None, AttachedFileEvent]:
            async with slots:
                return await AttachedFileReader.read(file, agent_class, agent_id, embedding_budget, section_cache)

        return list(await asyncio.gather(*(read_one(file) for file in files)))

    @staticmethod
    async def read(
        file: UserUploadedFile,
        agent_class: str,
        agent_id: str,
        embedding_budget: ModelTokenBudget,
        cache: AttachedFileSectionCache,
    ) -> tuple[AttachedFileText | None, AttachedFileEvent]:
        bucket, key = file.resolve_s3_location(agent_class, agent_id)
        try:
            text = await AttachedFileReader._cached(
                file, bucket, key, embedding_budget, cache
            ) or await AttachedFileReader._extracted(file, bucket, key, embedding_budget, cache)
        except Exception as error:
            logger.exception(f"[attached-files] Could not read {file.filename} ({file.file_id})")
            return None, AttachedFileEvent(
                file_id=file.file_id,
                filename=file.filename,
                citation_id=CitationId.of(file.file_id),
                status=AttachedFileStatus.FAILED,
                error=AttachedFileReader.describe_failure(error),
            )
        return text, AttachedFileEvent(
            file_id=file.file_id,
            filename=file.filename,
            citation_id=CitationId.of(file.file_id),
            status=AttachedFileStatus.READ,
            number_of_pages=text.number_of_pages,
        )

    @staticmethod
    def describe_failure(error: Exception) -> str:
        """Short enough for the model to repeat to the user; the full error is in the log."""
        message = str(error).splitlines()[0] if str(error) else type(error).__name__
        return message[:200]

    @staticmethod
    async def _cached(
        file: UserUploadedFile,
        bucket: str,
        key: str,
        embedding_budget: ModelTokenBudget,
        cache: AttachedFileSectionCache,
    ) -> AttachedFileText | None:
        """A record without its sections, which expire on their own, is read afresh."""
        record = await cache.record(bucket, key)
        if record is None:
            return None
        sections = await cache.sections(record.content_sha256, embedding_budget.tokenizer_id)
        if sections is None:
            return None
        return AttachedFileText(
            sections=AttachedFileSections.restamp(sections, file.file_id, file.filename, record.title),
            content_sha256=record.content_sha256,
            title=record.title,
            number_of_pages=record.number_of_pages,
            is_paged=record.is_paged,
        )

    @staticmethod
    async def _extracted(
        file: UserUploadedFile,
        bucket: str,
        key: str,
        embedding_budget: ModelTokenBudget,
        cache: AttachedFileSectionCache,
    ) -> AttachedFileText:
        """The same content uploaded again keeps its sections; only its record is new."""
        document = await DocumentExtractor.extract_from_s3(bucket, key, content_type=file.file_type)
        content_sha256 = hashlib.sha256(document.content.encode()).hexdigest()
        title = document.title or file.filename
        known = await cache.sections(content_sha256, embedding_budget.tokenizer_id)
        if known is None:
            sections = await asyncio.to_thread(
                AttachedFileSections.parse, document, file.file_id, file.filename, embedding_budget.model_name
            )
            await cache.put_sections(content_sha256, embedding_budget.tokenizer_id, sections)
        else:
            sections = AttachedFileSections.restamp(known, file.file_id, file.filename, title)
        record = AttachedFileRecord(
            content_sha256=content_sha256,
            title=title,
            number_of_pages=document.number_of_pages,
            is_paged=document.is_paged,
        )
        await cache.put_record(bucket, key, record)
        return AttachedFileText(sections=sections, **record.model_dump())
