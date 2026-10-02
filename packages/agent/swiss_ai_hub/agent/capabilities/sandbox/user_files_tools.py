import json
from typing import Annotated, Any

from llama_index.core.tools.tool_spec.base import BaseToolSpec
from swiss_ai_hub.core.events.agent import ChatFeature
from swiss_ai_hub.core.infrastructure import SandboxHomePath

from swiss_ai_hub.agent.capabilities.sandbox.sandbox_workspace import SandboxWorkspace
from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext
from swiss_ai_hub.agent.capabilities.tool_loop.tool_options import ToolOptions
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


def _options(tool: str) -> dict[str, Any]:
    return {
        "label": AgentLocaleString.from_i18n_path(f"agent.sandbox.user_files.{tool}.label"),
        "approval_summary": AgentLocaleString.from_i18n_path(f"agent.sandbox.user_files.{tool}.approval"),
        "chat_feature": ChatFeature.USER_FILES,
    }


class UserFilesTools(BaseToolSpec):
    """The user's own files, the ones My Files shows, to look through and read but not change.

    Offered while the user has My Files switched on in the chat. Paths are relative to the top of their file space,
    where each conversation's attachments lie under `conversations/`.
    """

    spec_functions = ["list_my_files", "read_my_file"]

    def __init__(self, context: ToolContext) -> None:
        self.context = context

    @ToolOptions.of(**_options("list_my_files"))
    async def list_my_files(self, folder: Annotated[str, "A folder in the user's files; '.' is the top."] = ".") -> str:
        """The files and folders in a folder of the user's own files, with sizes. Chat attachments lie under
        conversations/<conversation>/."""
        client = SandboxWorkspace.of(self.context).client
        listing = await client.list_files(SandboxHomePath.of(folder))
        entries = [entry for entry in listing.get("entries", []) if not entry["name"].startswith(".")]
        return json.dumps(entries, ensure_ascii=False)

    @ToolOptions.of(**_options("read_my_file"))
    async def read_my_file(
        self,
        path: Annotated[str, "The file's path in the user's files, e.g. reports/q1.pdf."],
        start_line: Annotated[int | None, "The first line to read, from 1."] = None,
        end_line: Annotated[int | None, "The last line to read."] = None,
    ) -> str:
        """Read one of the user's own files; PDF and office documents come back as their text."""
        client = SandboxWorkspace.of(self.context).client
        return json.dumps(await client.read_file(SandboxHomePath.of(path), start_line, end_line), ensure_ascii=False)
