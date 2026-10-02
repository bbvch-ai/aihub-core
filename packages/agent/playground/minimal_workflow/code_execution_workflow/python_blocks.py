import re
from typing import Annotated

from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import LLMEvent, Message, SandboxFileDisplayedEvent

from swiss_ai_hub.agent.capabilities import SandboxWorkspace


class PythonBlocks:
    """Runs the ```python blocks of a message one after another in the user's sandbox, each as its own script."""

    PATTERN = re.compile(r"```python[^\S\n]*\n(.*?)```", re.DOTALL)
    OUTPUT_FILE = "python_output.txt"

    @classmethod
    def in_text(cls, text: Annotated[str, "A chat message"]) -> list[str]:
        return [block.strip("\n") for block in cls.PATTERN.findall(text) if block.strip()]

    @classmethod
    async def run(cls, workspace: SandboxWorkspace, blocks: list[str]) -> tuple[str, SandboxFileDisplayedEvent]:
        """Each block's output, and the output written to a file in the conversation folder and kept for the user."""
        sections = []
        for number, code in enumerate(blocks, start=1):
            script = f"python_block_{number}.py"
            await workspace.client.write_file(workspace.path(script), code)
            result = await workspace.client.execute(f"python3 {script}", cwd=workspace.folder, wait=60)
            output = "".join(chunk.get("data", "") for chunk in result.get("output", [])).replace("\r\n", "\n")
            sections.append(f"Block {number} (exit code {result.get('exit_code')}):\n{output.rstrip()}")
        report = "\n\n".join(sections) + "\n"
        await workspace.client.write_file(workspace.path(cls.OUTPUT_FILE), report)
        return report, await workspace.keep(cls.OUTPUT_FILE)

    @staticmethod
    async def reply(displayer: EventDisplayer, text: str) -> LLMEvent:
        """A fixed reply shown as the answer and handed to the conversation like a model's, though none wrote it."""
        await displayer.display_chunk(text, model_name="python")
        return LLMEvent(output_messages=[Message.from_string("assistant", text)])
