import json
from pathlib import PurePosixPath

from swiss_ai_hub.core.generative_ai import DocumentExtractor
from swiss_ai_hub.core.infrastructure import OpenTerminalClient

from swiss_ai_hub.agent.capabilities.attached_files.attached_file_page_range import AttachedFilePageRange


class UserFilePages:
    """Certain pages of a document in the user's files, for a question about them.

    The sandbox reads a document as plain text by line, which knows nothing of pages. The file's bytes go through the
    platform's own extraction instead, which marks where pages break and caches a parse by content, so reading on
    through a long document costs one parse.
    """

    @staticmethod
    async def read(client: OpenTerminalClient, path: str, first_page: int, last_page: int | None) -> str:
        content, content_type = await client.view(path)
        document = await DocumentExtractor.extract_from_bytes(content, PurePosixPath(path).name, content_type)
        if not document.is_paged:
            return json.dumps(
                {"path": path, "error": "This file has no page numbers; read it by lines instead."}, ensure_ascii=False
            )
        pages = AttachedFilePageRange.of(first_page, last_page).within(document.number_of_pages)
        texts = document.pages(pages.first, pages.last)
        return json.dumps(
            {
                "path": path,
                "number_of_pages": document.number_of_pages,
                "pages": [{"page": pages.first + offset, "text": text} for offset, text in enumerate(texts)],
            },
            ensure_ascii=False,
        )
