from typing import Any

from llama_index.core import Document
from llama_index.core.readers.base import BaseReader

from aihub_lib.persistence.rag.vectors.node_metadata import NODE_CONTENT_TYPE_FIGURE, NUMBER_OF_PAGES


class ImageLoader(BaseReader):
    def _create_document(
        self,
        file: str,
        extra_info: dict | None = None,
    ):
        metadata = {NUMBER_OF_PAGES: 1}
        figure_tag = f"<{NODE_CONTENT_TYPE_FIGURE}>![]({file})</{NODE_CONTENT_TYPE_FIGURE}>"

        return [
            Document(
                text=figure_tag,
                extra_info={**extra_info, **metadata} if extra_info else metadata,
            )
        ]

    def load_data(
        self,
        file: str,
        extra_info: dict | None = None,
        **kwargs: Any,
    ):
        return self._create_document(file, extra_info)

    async def aload_data(
        self,
        file: str,
        extra_info: dict | None = None,
        **kwargs: Any,
    ):
        return self._create_document(file, extra_info)
