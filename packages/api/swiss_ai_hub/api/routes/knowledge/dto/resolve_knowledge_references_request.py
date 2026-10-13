from typing import Annotated

from pydantic import BaseModel, Field


class ResolveKnowledgeReferencesRequest(BaseModel):
    openwebui_ids: Annotated[
        list[str],
        Field(description="Ids of the OpenWebUI knowledge entries a chat message referenced.", max_length=100),
    ]
