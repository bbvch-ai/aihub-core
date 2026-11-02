from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.generative_ai import IngestedNode
from swiss_ai_hub.core.persistence import PAGE


class AttachedFilePageRange(BaseModel):
    """The pages a question is about. A file that knows its pages is read by them, in order, instead of by relevance,
    since no ranking can tell which section is "page 31"."""

    first: Annotated[int, Field(description="The first page, counted from 1.", ge=1)]
    last: Annotated[int, Field(description="The last page, never before the first.", ge=1)]

    @classmethod
    def of(cls, first_page: int | None, last_page: int | None) -> Self | None:
        if first_page is None:
            return None
        return cls(first=first_page, last=max(last_page or first_page, first_page))

    def select(self, sections: list[IngestedNode]) -> list[IngestedNode]:
        return [section for section in sections if self.first <= self.page_of(section) <= self.last]

    def within(self, number_of_pages: int | None) -> Self:
        """The range cut to the pages the file has, so a note never names a page past its end."""
        if number_of_pages is None:
            return self
        return self.model_copy(update={"last": max(min(self.last, number_of_pages), self.first)})

    @staticmethod
    def page_of(section: IngestedNode) -> int:
        return (section.metadata or {}).get(PAGE, 1)
