from pydantic import BaseModel


class UpdateNamespaceRequest(BaseModel):
    display_name: str | None = None
    description: str | None = None
