from typing import Annotated

from pydantic import BaseModel, Field


class KnowledgeReference(BaseModel):
    """A knowledge collection the user pointed the conversation at, e.g. with `#` in a chat client.

    A request, not a grant: the agent searches it only when the asking user may read it.
    """

    database: Annotated[str, Field(description="The knowledge database, by its vector collection name.", min_length=1)]
    namespace: Annotated[str, Field(description="The collection (namespace) within the database.", min_length=1)]
