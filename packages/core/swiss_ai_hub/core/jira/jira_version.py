from datetime import date
from typing import Annotated, Any, Self

from pydantic import BaseModel, Field


class JiraVersion(BaseModel):
    """One fix version of a project as Jira lists it, e.g. for an agent to recognise the release a chat message names.

    Versions belong to a project: two projects can each have a "2.4.0", which are two versions with two ids.
    """

    id: Annotated[str, Field(description="Jira's version id; a search by id needs no quoting and cannot be ambiguous.")]
    name: Annotated[str, Field(description="The version's name, e.g. 2.4.0 or 2026-Q3.")]
    project: Annotated[str, Field(description="Key of the project the version belongs to.")]
    released: Annotated[bool, Field(description="Whether the version is marked released.")] = False
    archived: Annotated[bool, Field(description="Whether the version is archived.")] = False
    release_date: Annotated[date | None, Field(description="The planned or actual release date, if set.")] = None

    @classmethod
    def from_answer(
        cls,
        answer: Annotated[dict[str, Any], "One entry of GET /rest/api/2/project/{key}/versions"],
        project: Annotated[str, "Key of the project the versions were listed for"],
    ) -> Self:
        return cls(
            id=str(answer["id"]),
            name=answer["name"],
            project=project,
            released=bool(answer.get("released")),
            archived=bool(answer.get("archived")),
            release_date=answer.get("releaseDate"),
        )
