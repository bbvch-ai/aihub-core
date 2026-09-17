"""
title: AI-Hub Capability Toggles
description: Relays OpenWebUI capability-toggle state to the AI-Hub agent and stops OpenWebUI running its own built-in implementation of a toggled capability for agent models.
required_open_webui_version: 0.6.0
"""

import logging
from typing import Annotated, Any, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Must stay in sync with ``AGENT_PIPE_ID_PREFIX`` in openwebui_provisioner.py — this filter must only
# ever touch agent pipe models, never plain LLM workspace models (those bypass the pipe and reach
# LiteLLM directly, where OpenWebUI's own feature handling works correctly and must be left alone).
AGENT_PIPE_ID_PREFIX = "aihub-pipeline."

# Deliberately not "features" — decouples the agent-facing contract from OpenWebUI's own request shape,
# and gives future capabilities with no native OpenWebUI feature key (e.g. Web Fetch) a place to land.
CAPABILITY_TOGGLES_METADATA_KEY = "capability_toggles"


class Filter:
    """Inlet filter that relays capability-toggle state to the agent and blocks OpenWebUI's own execution.

    OpenWebUI's chat UI offers capability toggle buttons (Web Search, Image Generation, Code Interpreter,
    ...) that, for a regular model, drive OpenWebUI's *own* implementation of that capability. For an
    AI-Hub agent model this collides with agents building native, traceable steps for the same
    capabilities: left alone, OpenWebUI runs its own forced handler for a toggled capability *before* the
    agent pipe is even invoked (``middleware.py``: inlet filters -> ``features = form_data.pop("features",
    ...)`` -> forced handlers -> only then dispatch to the pipe) — so the capability would execute twice
    once the agent grows a native step for it.

    Inlet filters are the only hook that runs early enough to intercept this; by the time the pipe's
    ``pipe()`` method runs, OpenWebUI's forced handlers have already fired. This filter therefore:
    - copies the raw toggle state into ``__metadata__["capability_toggles"]`` — the same dict object the
      pipe later receives as ``__metadata__``, so the copy survives the ``metadata.update()`` OpenWebUI
      does further down the same request
    - empties ``body["features"]`` so OpenWebUI's own forced handlers, and (in native function-calling
      mode) its builtin-tool injection, see nothing to act on

    Suppresses every toggled feature uniformly rather than allow-listing specific capability names: an
    agent pipe never benefits from OpenWebUI acting on its behalf, regardless of which feature OpenWebUI
    ships next.
    """

    class Valves(BaseModel):
        pass

    def __init__(self) -> None:
        self.valves = self.Valves()

    async def inlet(
        self,
        body: Annotated[dict[str, Any], "Inlet payload (model, messages, features, ...)"],
        __metadata__: Annotated[Optional[dict[str, Any]], "Request metadata"] = None,
        **kwargs: Any,
    ) -> Annotated[dict[str, Any], "Payload with capability toggles relocated and cleared"]:
        """Relay capability toggles to the agent and clear them so OpenWebUI does not act on them."""
        if not body.get("model", "").startswith(AGENT_PIPE_ID_PREFIX):
            return body

        features = body.get("features") or {}
        if not features:
            return body

        if __metadata__ is None:
            logger.warning("No request metadata available; capability toggles will not reach the agent")
            return body

        __metadata__[CAPABILITY_TOGGLES_METADATA_KEY] = dict(features)
        body["features"] = {}
        return body
