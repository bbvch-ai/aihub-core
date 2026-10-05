import json
from typing import Annotated, Any

from llama_index.core.tools.tool_spec.base import BaseToolSpec
from swiss_ai_hub.core.events.agent import ChatFeature

from swiss_ai_hub.agent.capabilities.sandbox.sandbox_workspace import SandboxWorkspace
from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext
from swiss_ai_hub.agent.capabilities.tool_loop.tool_options import ToolOptions
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


def _options(tool: str) -> dict[str, Any]:
    return {
        "label": AgentLocaleString.from_i18n_path(f"agent.sandbox.tools.{tool}.label"),
        "approval_summary": AgentLocaleString.from_i18n_path(f"agent.sandbox.tools.{tool}.approval"),
        "chat_feature": ChatFeature.CODE_INTERPRETER,
    }


class SandboxTools(BaseToolSpec):
    """The user's code sandbox as tools: the operations OpenWebUI's own terminal integration offers, run by the agent.

    Each runs in the asking user's sandbox home, in this conversation's folder, which holds the conversation's
    attached files. Offered only while the user has Code Interpreter switched on.
    """

    spec_functions = [
        "run_command",
        "get_process_status",
        "send_process_input",
        "kill_process",
        "list_processes",
        "list_files",
        "read_file",
        "write_file",
        "replace_file_content",
        "grep_search",
        "glob_search",
        "display_file",
    ]

    def __init__(self, context: ToolContext) -> None:
        self.context = context

    @ToolOptions.of(**_options("run_command"))
    async def run_command(
        self,
        command: Annotated[str, "A shell command; chaining, pipes and redirects work. Python 3 is installed."],
        wait: Annotated[int, "Seconds to wait for it to finish, at most 300; a longer run keeps going."] = 60,
    ) -> str:
        """Run a shell command in the user's code sandbox, in this conversation's folder, which holds the files
        attached to the conversation unchanged. Use it to run code, e.g. `python3 analysis.py`. Work on attached
        spreadsheets, presentations and CSV files here, where code reads them natively; documents such as PDF and
        Word files read better with the tool that reads attached files, which returns them as Markdown."""
        workspace = await self._workspace()
        result = await workspace.client.execute(command, cwd=workspace.folder, wait=min(max(wait, 0), 300))
        return self._process(result)

    @ToolOptions.of(**_options("get_process_status"))
    async def get_process_status(
        self,
        process_id: Annotated[str, "The id run_command returned for a command still running."],
        wait: Annotated[int, "Seconds to wait for it to finish, at most 300."] = 0,
    ) -> str:
        """The new output of a command still running in the sandbox, and whether it finished."""
        workspace = await self._workspace()
        return self._process(await workspace.client.process_status(process_id, wait=min(max(wait, 0), 300)))

    @ToolOptions.of(**_options("send_process_input"))
    async def send_process_input(
        self,
        process_id: Annotated[str, "The id of the running command."],
        text: Annotated[str, "What to type into it; end a line with a newline."],
    ) -> str:
        """Type into a command still running in the sandbox, such as an answer to a prompt it shows."""
        workspace = await self._workspace()
        return self._json(await workspace.client.send_input(process_id, text))

    @ToolOptions.of(**_options("kill_process"))
    async def kill_process(self, process_id: Annotated[str, "The id of the running command."]) -> str:
        """Stop a command still running in the sandbox."""
        workspace = await self._workspace()
        return self._json(await workspace.client.kill(process_id))

    @ToolOptions.of(**_options("list_processes"))
    async def list_processes(self) -> str:
        """The commands started in the sandbox and whether they still run."""
        workspace = await self._workspace()
        return self._json(await workspace.client.list_processes())

    @ToolOptions.of(**_options("list_files"))
    async def list_files(
        self, directory: Annotated[str, "A folder, relative to this conversation's folder or starting with ~/."] = "."
    ) -> str:
        """The files and folders in a sandbox folder, with their sizes."""
        workspace = await self._workspace()
        return self._json(await workspace.client.list_files(workspace.path(directory)))

    @ToolOptions.of(**_options("read_file"))
    async def read_file(
        self,
        path: Annotated[str, "The file, relative to this conversation's folder or starting with ~/."],
        start_line: Annotated[int | None, "The first line to read, from 1."] = None,
        end_line: Annotated[int | None, "The last line to read."] = None,
    ) -> str:
        """Read a text file from the sandbox; PDF and office documents come back as their text."""
        workspace = await self._workspace()
        return self._json(await workspace.client.read_file(workspace.path(path), start_line, end_line))

    @ToolOptions.of(**_options("write_file"))
    async def write_file(
        self,
        path: Annotated[str, "The file, relative to this conversation's folder or starting with ~/."],
        content: Annotated[str, "The file's whole text."],
    ) -> str:
        """Write a text file in the sandbox, creating its folders; an existing file is overwritten."""
        workspace = await self._workspace()
        return self._json(await workspace.client.write_file(workspace.path(path), content))

    @ToolOptions.of(**_options("replace_file_content"))
    async def replace_file_content(
        self,
        path: Annotated[str, "The file, relative to this conversation's folder or starting with ~/."],
        target: Annotated[str, "The exact text to find, whitespace included."],
        replacement: Annotated[str, "The text to put in its place."],
        allow_multiple: Annotated[bool, "Replace every occurrence instead of failing when there are several."] = False,
    ) -> str:
        """Replace a piece of a text file in the sandbox without rewriting the whole file."""
        workspace = await self._workspace()
        replacements = [{"target": target, "replacement": replacement, "allow_multiple": allow_multiple}]
        return self._json(await workspace.client.replace_file_content(workspace.path(path), replacements))

    @ToolOptions.of(**_options("grep_search"))
    async def grep_search(
        self,
        query: Annotated[str, "The text to look for."],
        path: Annotated[str, "Where to look, relative to this conversation's folder or starting with ~/."] = ".",
        regex: Annotated[bool, "Whether the query is a regular expression."] = False,
        case_insensitive: Annotated[bool, "Whether case is ignored."] = False,
    ) -> str:
        """Find lines containing a text in the sandbox's files."""
        workspace = await self._workspace()
        return self._json(await workspace.client.grep(query, workspace.path(path), regex, case_insensitive))

    @ToolOptions.of(**_options("glob_search"))
    async def glob_search(
        self,
        pattern: Annotated[str, "A file name pattern, e.g. **/*.csv."],
        path: Annotated[str, "Where to look, relative to this conversation's folder or starting with ~/."] = ".",
    ) -> str:
        """Find files by name in the sandbox."""
        workspace = await self._workspace()
        return self._json(await workspace.client.glob(pattern, workspace.path(path)))

    @ToolOptions.of(**_options("display_file"))
    async def display_file(
        self, path: Annotated[str, "The file, relative to this conversation's folder or starting with ~/."]
    ) -> str:
        """Show the user a file from the sandbox, attached to your answer for them to open or download. Use it for
        every file you made for the user, such as a chart, a spreadsheet or a document. Its download link is added
        below your answer by itself; never write a link or path to it yourself, since such links do not work."""
        workspace = await self._workspace()
        displayed = await workspace.keep(path)
        await self.context.displayer.display_event(displayed)
        return f"Attached {displayed.filename} ({displayed.size} bytes) to your answer for the user."

    async def _workspace(self) -> SandboxWorkspace:
        workspace = SandboxWorkspace.of(self.context)
        await workspace.prepare()
        return workspace

    @staticmethod
    def _process(result: dict[str, Any]) -> str:
        output = "".join(chunk.get("data", "") for chunk in result.get("output", [])).replace("\r\n", "\n")
        if result.get("status") == "running":
            head = f"Still running as process {result['id']}; check on it with get_process_status."
        else:
            head = f"Exit code {result.get('exit_code')}."
        truncated = " The output was cut; earlier lines are not shown." if result.get("truncated") else ""
        return f"{head}{truncated}\n{output}".rstrip()

    @staticmethod
    def _json(result: Any) -> str:
        return json.dumps(result, ensure_ascii=False)
