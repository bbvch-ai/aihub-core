"""
title: AI-Hub Chat Features
description: Hands the chat toggles an agent supports to the AI-Hub pipe, so OpenWebUI never runs its own web search, image generation or code interpreter for agents.
required_open_webui_version: 0.11.0
global: false
"""

import logging
from typing import Annotated, Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Must stay in sync with ``aihub_pipeline.py``, which forwards this list as the agent's requested features, and
# with our toggle filters for features OpenWebUI has no toggle for, which add their feature to the same list.
REQUESTED_FEATURES_METADATA_KEY = "aihub_requested_features"

# OpenWebUI's native toggles, named as in ``ChatFeature`` and in the model capabilities that show them.
NATIVE_FEATURES = ("web_search", "image_generation", "code_interpreter")

# Features OpenWebUI serves itself that an agent never receives: our agents recall their own memories.
OPENWEBUI_ONLY_FEATURES = ("memory",)


class Filter:
    """Inlet filter, attached to agent models only, that turns OpenWebUI's chat toggles into a request to the agent.

    OpenWebUI acts on ``body["features"]`` right after the inlet filters ran: it searches the web, generates images
    and rewrites the prompt for the code interpreter before the pipe is ever called. Taking the toggles out of the
    body here is the one point that stops all of it, whatever the model's function-calling mode.

    A toggle's state is sent even when the selected model does not show it, e.g. after switching models in a chat,
    so a feature is forwarded only when the selected model's capabilities, which the AI-Hub provisioner writes from
    the agent's blueprint, say the agent supports it.
    """

    class Valves(BaseModel):
        priority: Annotated[int, Field(description="Filter execution order; lower runs first.")] = 0

    def __init__(self) -> None:
        self.valves = self.Valves()

    async def inlet(
        self,
        body: Annotated[dict[str, Any], "Completion payload; ``features`` holds the chat toggles"],
        __metadata__: Annotated[dict[str, Any] | None, "Request metadata, handed to the pipe unchanged"] = None,
        __model__: Annotated[dict[str, Any] | None, "Resolved model with its capabilities"] = None,
        **kwargs: Any,
    ) -> Annotated[dict[str, Any], "Payload without the features OpenWebUI would otherwise act on"]:
        """Move the supported toggles into the metadata for the pipe and strip every toggle from the body."""
        features = dict(body.get("features") or {})
        supported = self._supported_native_features(__model__)
        requested = {feature for feature in NATIVE_FEATURES if features.get(feature) and feature in supported}

        for feature in (*NATIVE_FEATURES, *OPENWEBUI_ONLY_FEATURES):
            features.pop(feature, None)
        body["features"] = features

        if __metadata__ is not None:
            already_requested = set(__metadata__.get(REQUESTED_FEATURES_METADATA_KEY) or [])
            __metadata__[REQUESTED_FEATURES_METADATA_KEY] = sorted(already_requested | requested)
        return body

    @staticmethod
    def _supported_native_features(
        model: Annotated[dict[str, Any] | None, "Resolved model"],
    ) -> Annotated[set[str], "Native features whose capability is explicitly on for this model"]:
        capabilities = (((model or {}).get("info") or {}).get("meta") or {}).get("capabilities") or {}
        return {feature for feature in NATIVE_FEATURES if capabilities.get(feature) is True}
