import logging

from swiss_ai_hub.core.events.agent import AttachedFileEvent, AttachedFileStatus, UserUploadedFile
from swiss_ai_hub.core.generative_ai import DocumentExtractor, ExtractedDocument

logger = logging.getLogger(__name__)

EXCERPT_CHARACTERS = 500


class AttachedFileReader:
    """Reads one attached file out of the agent's upload bucket into text, reporting a file that cannot be read.

    A failure is an outcome, not an exception: the user asked about the file, so an unreadable one must end in an
    answer that says so, and one bad file must not take the other attachments of the turn down with it.
    """

    @staticmethod
    def is_readable_attachment(file: UserUploadedFile) -> bool:
        """Images already reach the model as image content in the message, so they are not read as documents."""
        return not file.file_type.startswith("image/")

    @staticmethod
    async def read(
        file: UserUploadedFile, agent_class: str, agent_id: str
    ) -> tuple[ExtractedDocument | None, AttachedFileEvent]:
        bucket, key = file.resolve_s3_location(agent_class, agent_id)
        try:
            document = await DocumentExtractor.extract_from_s3(bucket, key, content_type=file.file_type)
        except Exception as error:
            logger.exception(f"[attached-files] Could not read {file.filename} ({file.file_id})")
            return None, AttachedFileEvent(
                file_id=file.file_id,
                filename=file.filename,
                status=AttachedFileStatus.FAILED,
                error=AttachedFileReader.describe_failure(error),
            )
        return document, AttachedFileEvent(
            file_id=file.file_id,
            filename=file.filename,
            status=AttachedFileStatus.READ,
            number_of_pages=document.number_of_pages,
            excerpt=document.content[:EXCERPT_CHARACTERS],
        )

    @staticmethod
    def describe_failure(error: Exception) -> str:
        """Short enough for the model to repeat to the user; the full error is in the log."""
        message = str(error).splitlines()[0] if str(error) else type(error).__name__
        return message[:200]
