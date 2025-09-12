from typing import Any

from fsspec import AbstractFileSystem
from llama_index.core import Document
from llama_index.core.readers.base import BaseReader

from aihub_lib.persistence.rag.vectors.node_metadata import NODE_CONTENT_TYPE_FIGURE, NUMBER_OF_PAGES


class ImageLoader(BaseReader):

    def load_data(
        self,
        file: str,
        extra_info: dict | None = None,
        fs: AbstractFileSystem | None = None,
        figures_directory_name: str | None = None,
    ):
        metadata = {NUMBER_OF_PAGES: 1}
        figure_tag = f"<{NODE_CONTENT_TYPE_FIGURE}>![]({file})</{NODE_CONTENT_TYPE_FIGURE}>"

        return [
            Document(
                text=figure_tag,
                extra_info={**extra_info, **metadata} if extra_info else metadata,
            )
        ]
