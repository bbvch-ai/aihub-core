"""
title: AI-Hub Turn File Scope
description: Limits the OpenWebUI file context to the files attached to the message being answered, so an agent stops answering about documents from earlier turns.
required_open_webui_version: 0.6.0
"""

import logging
from typing import Annotated, Any

from open_webui.models.chats import Chats
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Must stay in sync with ``openwebui_provisioner.AIHUB_AGENT_PREFIX``: workspace models the provisioner creates
# for agents carry this prefix, and they are the models whose file context reaches the AI-Hub pipe.
AIHUB_AGENT_PREFIX = "aihub-agent-"


class Filter:
    """Inlet filter that scopes ``body["files"]`` to the current turn.

    OpenWebUI hands every file of the conversation to the completion on every turn: the frontend sends the
    accumulated list as ``files``, ``process_chat_payload`` moves it into ``metadata["files"]`` *after* the inlet
    filters ran, and from there it feeds both ``chat_completion_files_handler`` — which, with ``RAG_FULL_CONTEXT``,
    inlines every listed document into the user message — and the ``__files__`` the pipe forwards to the agent.
    Nothing downstream can tell a file attached to this message from one attached ten turns ago, which is how an
    agent ends up summarising the wrong document (aihub-core-private#147).

    The message being answered is the one place that knows its own attachments. The frontend sends it whole as
    ``user_message`` (``main.py``: ``metadata["user_message"]``); for callers that do not, the chat row keeps the
    per-message ``files`` list, reachable through the assistant message's ``parentId``. When neither can be
    established the list is left untouched, so a client this filter does not recognise behaves exactly as before.

    Attaching a file is read as "talk about this": a turn that attaches files keeps only those files; a turn that
    attaches nothing keeps the whole list, so follow-up questions about earlier documents still work. Only
    ``type == "file"`` items are scoped — knowledge collections, notes and web-search hits are attached with a
    different intent and are left in place.
    """

    class Valves(BaseModel):
        priority: Annotated[int, Field(description="Filter execution order; lower runs first.")] = 0
        agent_models_only: Annotated[
            bool,
            Field(
                description="Scope only workspace models the AI-Hub provisioner created for agents "
                f"(``{AIHUB_AGENT_PREFIX}*``). Disable to scope plain LLM models too."
            ),
        ] = True

    def __init__(self) -> None:
        self.valves = self.Valves()

    async def inlet(
        self,
        body: Annotated[dict[str, Any], "Completion payload; ``files`` is the whole conversation's list"],
        __metadata__: Annotated[dict[str, Any] | None, "Request metadata"] = None,
        __model__: Annotated[dict[str, Any] | None, "Resolved model"] = None,
        **kwargs: Any,
    ) -> Annotated[dict[str, Any], "Payload with ``files`` scoped to the current turn"]:
        """Drop files attached in earlier turns when the message being answered attaches files of its own."""
        files = body.get("files") or []
        if not files or not self._applies_to(__model__):
            return body

        current_turn_ids = await self._current_turn_file_ids(__metadata__ or {})
        if not current_turn_ids:
            return body

        scoped = [file for file in files if file.get("type", "file") != "file" or file.get("id") in current_turn_ids]
        logger.debug(
            f"Scoped files for chat {(__metadata__ or {}).get('chat_id')}: {len(files)} in conversation, "
            f"{len(scoped)} kept for this turn"
        )
        body["files"] = scoped
        return body

    def _applies_to(self, model: Annotated[dict[str, Any] | None, "Resolved model"]) -> bool:
        if not self.valves.agent_models_only:
            return True
        return str((model or {}).get("id") or "").startswith(AIHUB_AGENT_PREFIX)

    @staticmethod
    async def _current_turn_file_ids(
        metadata: Annotated[dict[str, Any], "Request metadata"],
    ) -> Annotated[set[str], "OpenWebUI file ids attached to the message being answered; empty when unknown"]:
        user_message = metadata.get("user_message")
        if user_message is None:
            user_message = await Filter._user_message_from_chat(metadata)
        if user_message is None:
            return set()
        return {
            file["id"]
            for file in user_message.get("files") or []
            if file.get("id") and file.get("type", "file") == "file"
        }

    @staticmethod
    async def _user_message_from_chat(
        metadata: Annotated[dict[str, Any], "Request metadata"],
    ) -> Annotated[dict[str, Any] | None, "Stored user message being answered, if the chat row has it"]:
        """Fallback for callers that omit ``user_message``: walk from the assistant message to its parent.

        The parent link is what stays right when the user edits or regenerates a turn. A chat that is not
        persisted (``local:``/``channel:``) or a message the row does not hold yet yields ``None``.
        """
        chat_id = metadata.get("chat_id")
        if not chat_id or chat_id.startswith(("local:", "channel:")):
            return None

        user_message_id = metadata.get("user_message_id")
        if not user_message_id and metadata.get("message_id"):
            assistant_message = await Chats.get_message_by_id_and_message_id(chat_id, metadata["message_id"])
            user_message_id = (assistant_message or {}).get("parentId")
        if not user_message_id:
            return None
        return await Chats.get_message_by_id_and_message_id(chat_id, user_message_id)
