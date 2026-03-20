from typing import Any

from llama_index.core import Document
from llama_index.core.readers.base import BaseReader

from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NODE_CONTENT_TYPE_FIGURE, NUMBER_OF_PAGES


class ImageLoader(BaseReader):
    """
    A custom document loader for image files that creates a Document with an HTML figure tag.
    This loader does not perform any OCR or image analysis; it simply wraps the image in a figure tag.
    Useful for pipeline ingestion where we generate descriptions for embeddings.
    """

    def load_data(
        self,
        file: str,
        extra_info: dict | None = None,
        **kwargs: Any,
    ):
        metadata = {NUMBER_OF_PAGES: 1}
        figure_tag = f"<{NODE_CONTENT_TYPE_FIGURE}>![]({file})</{NODE_CONTENT_TYPE_FIGURE}>"

        return [
            Document(
                text=figure_tag,
                extra_info={**extra_info, **metadata} if extra_info else metadata,
            )
        ]
