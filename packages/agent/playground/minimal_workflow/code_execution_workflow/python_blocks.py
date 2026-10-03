import re
from typing import Annotated, Any, ClassVar

from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import LLMEvent, Message, SandboxFileDisplayedEvent
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.capabilities import SandboxWorkspace


class PythonBlocks:
    """Runs the ```python blocks of a message one after another in the user's sandbox, each as its own script."""

    PATTERN = re.compile(r"```python[^\S\n]*\n(.*?)```", re.DOTALL)
    OUTPUT_FILE = "python_output.txt"
    WAIT_SECONDS = 60
    FINISHED: ClassVar[LocaleString] = LocaleString(
        en="Block {number} (exit code {exit_code}):",
        de="Block {number} (Exit-Code {exit_code}):",
        fr="Bloc {number} (code de sortie {exit_code}) :",
        it="Blocco {number} (codice di uscita {exit_code}):",
    )
    STOPPED: ClassVar[LocaleString] = LocaleString(
        en="Block {number} (stopped after {seconds} seconds):",
        de="Block {number} (nach {seconds} Sekunden abgebrochen):",
        fr="Bloc {number} (arrêté après {seconds} secondes) :",
        it="Blocco {number} (interrotto dopo {seconds} secondi):",
    )

    @classmethod
    def in_text(cls, text: Annotated[str, "A chat message"]) -> list[str]:
        return [block.strip("\n") for block in cls.PATTERN.findall(text) if block.strip()]

    @classmethod
    async def run(
        cls, workspace: SandboxWorkspace, blocks: list[str], locale: str
    ) -> tuple[str, SandboxFileDisplayedEvent]:
        """Each block's output, and the output written to a file in the conversation folder and kept for the user.

        A block still running after the wait is stopped, so the next block never runs next to it."""
        sections = []
        for number, code in enumerate(blocks, start=1):
            script = f"python_block_{number}.py"
            await workspace.client.write_file(workspace.path(script), code)
            result = await workspace.client.execute(f"python3 {script}", cwd=workspace.folder, wait=cls.WAIT_SECONDS)
            if result.get("status") == "running":
                await workspace.client.kill(result["id"], force=True)
            output = "".join(chunk.get("data", "") for chunk in result.get("output", [])).replace("\r\n", "\n")
            sections.append(f"{cls._header(result, number, locale)}\n{output.rstrip()}")
        report = "\n\n".join(sections) + "\n"
        await workspace.client.write_file(workspace.path(cls.OUTPUT_FILE), report)
        return report, await workspace.keep(cls.OUTPUT_FILE)

    @classmethod
    def _header(cls, result: dict[str, Any], number: int, locale: str) -> str:
        if result.get("status") == "running":
            return cls.text(cls.STOPPED, locale, number=number, seconds=cls.WAIT_SECONDS)
        return cls.text(cls.FINISHED, locale, number=number, exit_code=result.get("exit_code"))

    @staticmethod
    def text(template: LocaleString, locale: str, **values: Any) -> str:
        return (template.in_locale(locale) or "").format(**values)

    @staticmethod
    async def reply(displayer: EventDisplayer, text: str) -> LLMEvent:
        """A fixed reply shown as the answer and handed to the conversation like a model's, though none wrote it."""
        await displayer.display_chunk(text, model_name="python")
        return LLMEvent(output_messages=[Message.from_string("assistant", text)])
