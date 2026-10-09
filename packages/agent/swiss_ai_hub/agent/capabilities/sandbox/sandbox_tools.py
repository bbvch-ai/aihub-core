import json
import posixpath
from typing import Annotated, Any

from llama_index.core.tools.tool_spec.base import BaseToolSpec
from swiss_ai_hub.core.events.agent import ChatFeature

from swiss_ai_hub.agent.capabilities.sandbox.sandbox_workspace import SandboxWorkspace
from swiss_ai_hub.agent.capabilities.structured_file import StructuredFile
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
        command: Annotated[
            str, "A shell command, e.g. `python3 -c '...'` or `python3 script.py`; chaining, pipes and redirects work."
        ],
        wait: Annotated[int, "Seconds to wait for it to finish, at most 300; a longer run keeps going."] = 60,
    ) -> str:
        """Run a shell command in the user's code sandbox, in this conversation's folder.

        The folder holds the files attached to the conversation, unchanged, and keeps every file you write between
        calls. Python 3 is installed with pandas, numpy, openpyxl, xlsxwriter, matplotlib, python-docx and
        python-pptx.
        - Use it to compute, convert or create files, and for attached spreadsheets, presentations and CSV files,
          which code reads natively. Read documents such as PDF and Word files with the tool for attached files.
        - Print what the next step needs, such as counts, totals or the first rows, not whole tables: long output is
          cut.
        - The result says whether the command succeeded and which files it created or changed. A command that
          succeeded has done its work: do not run it again unless you changed it or need its effect again.
        - A file you made for the user only reaches them through display_file."""
        workspace = await self._workspace()
        before = await self._files(workspace)
        result = await workspace.client.execute(command, cwd=workspace.folder, wait=min(max(wait, 0), 300))
        changed = self._changed(before, await self._files(workspace))
        return self._process(result) + changed

    @ToolOptions.of(**_options("get_process_status"))
    async def get_process_status(
        self,
        process_id: Annotated[str, "The id run_command returned for a command still running."],
        wait: Annotated[int, "Seconds to wait for it to finish, at most 300."] = 0,
    ) -> str:
        """Check on a command that run_command left running: its output since the last check, and whether it
        finished. Use it only with the process id run_command returned; pass wait to block until it finishes, for at
        most 300 seconds."""
        workspace = await self._workspace()
        return self._process(await workspace.client.process_status(process_id, wait=min(max(wait, 0), 300)))

    @ToolOptions.of(**_options("send_process_input"))
    async def send_process_input(
        self,
        process_id: Annotated[str, "The id of the running command."],
        text: Annotated[str, "What to type into it; end a line with a newline."],
    ) -> str:
        """Type into a command that run_command left running and that waits for input, such as an answer to a
        prompt it showed. End a line with a newline. Prefer commands that need no input."""
        workspace = await self._workspace()
        return self._json(await workspace.client.send_input(process_id, text))

    @ToolOptions.of(**_options("kill_process"))
    async def kill_process(self, process_id: Annotated[str, "The id of the running command."]) -> str:
        """Stop a command that run_command left running, for example one that hangs or is no longer needed. Its
        files stay as they are."""
        workspace = await self._workspace()
        return self._json(await workspace.client.kill(process_id))

    @ToolOptions.of(**_options("list_processes"))
    async def list_processes(self) -> str:
        """The commands started in the sandbox with their process ids and whether they still run. Use it to find
        a command you left running; you do not need it after a command that finished."""
        workspace = await self._workspace()
        return self._json(await workspace.client.list_processes())

    @ToolOptions.of(**_options("list_files"))
    async def list_files(
        self, directory: Annotated[str, "A folder, relative to this conversation's folder or starting with ~/."] = "."
    ) -> str:
        """The files and folders in a sandbox folder, with their sizes. Use it to find the exact name of an
        attached file or of a file a command made; run_command already reports the files it created or changed."""
        workspace = await self._workspace()
        return self._json(await workspace.client.list_files(workspace.path(directory)))

    @ToolOptions.of(**_options("read_file"))
    async def read_file(
        self,
        path: Annotated[str, "The file, relative to this conversation's folder or starting with ~/."],
        start_line: Annotated[int | None, "The first line to read, from 1."] = None,
        end_line: Annotated[int | None, "The last line to read."] = None,
    ) -> str:
        """Read a text file from the sandbox, or the lines asked for; PDF and Word documents come back as their text.

        Use it to look at a script, a log or the first lines of a CSV file. Spreadsheets and presentations are not
        read as text: process them with run_command, where code opens them natively."""
        if StructuredFile.is_binary(path):
            return (
                f"{posixpath.basename(path)} is a spreadsheet or presentation, which loses its structure as text. "
                "Open it with code in run_command instead, for example with pandas or python-pptx."
            )
        workspace = await self._workspace()
        return self._json(await workspace.client.read_file(workspace.path(path), start_line, end_line))

    @ToolOptions.of(**_options("write_file"))
    async def write_file(
        self,
        path: Annotated[str, "The file, relative to this conversation's folder or starting with ~/."],
        content: Annotated[str, "The file's whole text."],
    ) -> str:
        """Write a text file in the sandbox, such as a script or a CSV you build, creating its folders; an
        existing file is overwritten. To create a spreadsheet, document or chart, write and run code with
        run_command instead. A file you write only reaches the user through display_file."""
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
        """Change a piece of a text file in the sandbox, such as a line of a script, without rewriting the whole
        file. The target must match the file's text exactly, whitespace included; it fails when the text is missing
        or found several times, unless allow_multiple is set."""
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
        """Find the lines that contain a text in the sandbox's text files, with file names and line numbers. Use
        it to locate something in scripts, logs or CSV files; to analyse data, run code with run_command."""
        workspace = await self._workspace()
        return self._json(await workspace.client.grep(query, workspace.path(path), regex, case_insensitive))

    @ToolOptions.of(**_options("glob_search"))
    async def glob_search(
        self,
        pattern: Annotated[str, "A file name pattern, e.g. **/*.csv."],
        path: Annotated[str, "Where to look, relative to this conversation's folder or starting with ~/."] = ".",
    ) -> str:
        """Find files in the sandbox by a name pattern, such as **/*.xlsx, and get their paths. Use it when you
        know part of a name but not where the file lies."""
        workspace = await self._workspace()
        return self._json(await workspace.client.glob(pattern, workspace.path(path)))

    @ToolOptions.of(**_options("display_file"))
    async def display_file(
        self, path: Annotated[str, "The file, relative to this conversation's folder or starting with ~/."]
    ) -> str:
        """Attach a file from the sandbox to your answer, for the user to open or download. The user cannot see the
        sandbox, so this is the only way a file you made reaches them: call it once for every file you made for the
        user, such as a chart, a spreadsheet or a document, as soon as the command that made it succeeded. Its
        download link is added below your answer by itself; never write a link or a path to it yourself, since such
        links do not work."""
        workspace = await self._workspace()
        displayed = await workspace.keep(path)
        await self.context.displayer.display_event(displayed)
        return (
            f"Attached {displayed.filename} ({displayed.size} bytes) to your answer; the user gets it with a download "
            "link, so do not attach it again."
        )

    async def _workspace(self) -> SandboxWorkspace:
        workspace = SandboxWorkspace.of(self.context)
        await workspace.prepare()
        return workspace

    @staticmethod
    def _process(result: dict[str, Any]) -> str:
        output = "".join(chunk.get("data", "") for chunk in result.get("output", [])).replace("\r\n", "\n")
        if result.get("status") == "running":
            head = f"Still running as process {result['id']}; check on it with get_process_status."
        elif result.get("exit_code") == 0:
            head = "Command finished successfully (exit code 0)." + ("" if output.strip() else " It printed nothing.")
        else:
            head = f"Command failed (exit code {result.get('exit_code')}). Read the error below and fix the command."
        truncated = (
            " The output was cut; earlier lines are not shown. Print less, or write the output to a file and search it."
            if result.get("truncated")
            else ""
        )
        return f"{head}{truncated}\n{output}".rstrip()

    @staticmethod
    async def _files(workspace: SandboxWorkspace) -> dict[str, tuple[Any, Any]]:
        """The conversation folder's files by name, with what tells a changed one apart: its size and its time."""
        listing = await workspace.client.list_files(workspace.folder)
        return {
            entry["name"]: (entry.get("size"), entry.get("modified"))
            for entry in listing.get("entries", [])
            if entry.get("type") != "directory" and not entry["name"].startswith(".")
        }

    @staticmethod
    def _changed(before: dict[str, tuple[Any, Any]], after: dict[str, tuple[Any, Any]]) -> str:
        """Names the files a command made or changed, so the model knows its result without listing the folder."""
        changed = [name for name, stamp in sorted(after.items()) if before.get(name) != stamp]
        if not changed:
            return ""
        files = ", ".join(f"{name} ({SandboxTools._size(after[name][0])})" for name in changed)
        return (
            f"\nFiles created or changed in the conversation folder: {files}. "
            "Attach one for the user with display_file."
        )

    @staticmethod
    def _size(size: Any) -> str:
        if not isinstance(size, int):
            return "size unknown"
        if size < 1024:
            return f"{size} bytes"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size / (1024 * 1024):.1f} MB"

    @staticmethod
    def _json(result: Any) -> str:
        return json.dumps(result, ensure_ascii=False)
