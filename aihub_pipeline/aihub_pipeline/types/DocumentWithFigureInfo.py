from llama_index.core import Document
from pydantic import computed_field


class DocumentWithFigureInfo(Document):
    """Document with additional figure information, inheriting from llama_index Document.

    This class extends the llama_index Document with fields needed for figure processing.
    It keeps the document operations in the Document space until the final conversion
    to RefDocDocument at the end of the pipeline.
    """

    @computed_field
    @property
    def operation_id(self) -> str | None:
        return self.metadata.get("operation_id", None)

    @computed_field
    @property
    def figure_ids(self) -> list[str]:
        return self.metadata.get("figure_ids", [])
