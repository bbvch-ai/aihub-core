import logging
import mimetypes

from llama_index.core.readers.base import BaseReader

from swiss_ai_hub.core.generative_ai.document.loaders.mark_it_down_loader import MarkItDownLoader
from swiss_ai_hub.core.generative_ai.document.loaders.mineru_loader import MineruLoader
from swiss_ai_hub.core.generative_ai.document.loaders.raw_loader import RawLoader
from swiss_ai_hub.core.infrastructure.mineru.mineru_settings import MineruSettings

logger = logging.getLogger(__name__)


class DocumentLoaderSelector:
    """Maps a file to the loader that can read it: plaintext to `RawLoader`, PDFs and images to `MineruLoader`,
    Office documents to `MarkItDownLoader`.

    The routing itself is not new — it is inlined in the API's `ParsingService` and, in a configurable form, in the
    pipeline's `DocumentParserResource`. This is deliberately a third statement of it rather than the one both of
    those were migrated onto: `ParsingService` also routes `PASSTHROUGH_EXTENSIONS` to an empty response and answers
    an unknown extension with an `HTTPException` carrying the supported list, and `DocumentParserResource` swaps the
    whole map on `loader_type` for its Document-Intelligence mode. Neither collapses into this without changing
    behaviour those call sites are relied on for. What lives here instead is the extension lists staying owned by the
    loaders, so a fourth caller has something to reuse. Migrating the other two is worth doing; it is not this
    change's to do.

    Deliberately returns `None` for an unsupported extension rather than raising: the API answers a caller with 400,
    an agent skips the file and drafts without it. Turning "cannot read this" into an exception here would force one
    of those two to catch it.
    """

    @staticmethod
    def extension_for(filename: str, content_type: str = "") -> str | None:
        """Resolve the extension from the filename, falling back to the MIME type when the name carries none.

        Mail attachments are the reason the fallback exists: a part can arrive as `attachment` with a
        `Content-Type` and no usable filename.
        """
        if "." in filename:
            extension = filename.rsplit(".", 1)[-1].lower()
            if extension:
                return extension

        bare_content_type = content_type.split(";")[0].strip()
        if not bare_content_type:
            return None

        guessed = mimetypes.guess_extension(bare_content_type, strict=False)
        return guessed.lstrip(".").lower() if guessed else None

    @staticmethod
    def for_extension(extension: str | None) -> BaseReader | None:
        """Return a loader instance for `extension`, or `None` when nothing here can read it.

        The chain order matches `ParsingService` — raw, then MinerU, then MarkItDown. The three extension lists do
        not currently overlap, so the order changes nothing today; it is preserved so that if one ever does, both
        call sites resolve it the same way rather than silently diverging.
        """
        if not extension:
            return None

        extension = extension.lower().lstrip(".")
        if extension in RawLoader.SUPPORTED_EXTENSIONS:
            return RawLoader()
        if extension in MineruSettings().EXTENSIONS:
            return MineruLoader()
        if extension in MarkItDownLoader.SUPPORTED_EXTENSIONS:
            return MarkItDownLoader()

        logger.debug("[loader-selector] no loader handles extension %r", extension)
        return None

    @staticmethod
    def for_file(filename: str, content_type: str = "") -> BaseReader | None:
        """Resolve extension and loader in one call — what a caller holding only a filename and MIME type wants."""
        return DocumentLoaderSelector.for_extension(
            DocumentLoaderSelector.extension_for(filename, content_type),
        )
