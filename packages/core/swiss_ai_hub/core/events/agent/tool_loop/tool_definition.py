from typing import Annotated, Any

from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    """A tool as the model is offered it: what it is called, what it does and which arguments it takes."""

    name: Annotated[str, Field(description="The name the model calls the tool by.", pattern=r"^[a-zA-Z0-9_-]{1,64}$")]
    description: Annotated[str, Field(description="What the tool does and when to use it, for the model.")]
    parameters: Annotated[dict[str, Any], Field(description="JSON schema of the tool's arguments.")]

    def to_openai(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {"name": self.name, "description": self.description, "parameters": self.parameters},
        }
