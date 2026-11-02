from typing import Annotated

from pydantic import BaseModel, Field


class MediaWikiCollections(BaseModel):
    """Where a wiki's content lands in the knowledge database: one collection per synced namespace, and one for the
    files when they are synced.

    Collections are named after a namespace's canonical name, which a wiki reports next to the local one: English for
    the built-in namespaces (``File``, ``Project``) and as configured for custom ones. A change of the wiki's language
    or site name renames the local names only, so it moves nothing. The main namespace has no name and is ``Main``.
    """

    pages: Annotated[dict[int, str], Field(description="Namespace numbers to sync, with their collection names.")]
    files: Annotated[str | None, Field(description="Collection of the files; None when files are not synced.")] = None
