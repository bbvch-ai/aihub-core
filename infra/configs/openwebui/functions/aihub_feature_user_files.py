"""
title: My Files
description: Lets the AI-Hub agent read your own files, the attachments, generated files and uploads in My Files.
required_open_webui_version: 0.11.0
global: false
"""

from typing import Annotated, Any

from pydantic import BaseModel, Field

# Must stay in sync with ``aihub_feature_filter.py`` and ``aihub_pipeline.py``.
REQUESTED_FEATURES_METADATA_KEY = "aihub_requested_features"
FEATURE = "user_files"


class Filter:
    """A chat toggle for the user's own files, which OpenWebUI has no native toggle for.

    OpenWebUI runs a toggle filter only while the user has it switched on, so running at all is the request.
    """

    class Valves(BaseModel):
        priority: Annotated[int, Field(description="Filter execution order; lower runs first.")] = 0

    def __init__(self) -> None:
        self.valves = self.Valves()
        self.toggle = True
        self.icon = (
            "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIGZpbGw9Im5vbmUiIHZpZXdCb3g9"
            "IjAgMCAyNCAyNCIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZT0iY3VycmVudENvbG9yIj48cGF0aCBzdHJva2UtbGluZWNhcD0icm91"
            "bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIGQ9Ik0yLjI1IDEyLjc1VjEyQTIuMjUgMi4yNSAwIDAgMSA0LjUgOS43NWgxNWEyLjI1"
            "IDIuMjUgMCAwIDEgMi4yNSAyLjI1di43NW0tOC42OS02LjQ0LTIuMTItMi4xMmExLjUgMS41IDAgMCAwLTEuMDYxLS40NEg0LjVBMi4y"
            "NSAyLjI1IDAgMCAwIDIuMjUgNnYxMmEyLjI1IDIuMjUgMCAwIDAgMi4yNSAyLjI1aDE1QTIuMjUgMi4yNSAwIDAgMCAyMS43NSAxOFY5"
            "YTIuMjUgMi4yNSAwIDAgMC0yLjI1LTIuMjVoLTUuMzc5YTEuNSAxLjUgMCAwIDEtMS4wNi0uNDRaIiAvPjwvc3ZnPg=="
        )

    async def inlet(
        self,
        body: Annotated[dict[str, Any], "Completion payload"],
        __metadata__: Annotated[dict[str, Any] | None, "Request metadata, handed to the pipe unchanged"] = None,
        **kwargs: Any,
    ) -> Annotated[dict[str, Any], "The payload, unchanged"]:
        if __metadata__ is not None:
            already_requested = set(__metadata__.get(REQUESTED_FEATURES_METADATA_KEY) or [])
            __metadata__[REQUESTED_FEATURES_METADATA_KEY] = sorted(already_requested | {FEATURE})
        return body
