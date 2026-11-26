from pydantic import BaseModel
from swiss_ai_hub.core.events.agent import AttachedFileEvent
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.capabilities.attached_files.attached_file_fit_mode import FitMode


class AttachedFileCutNote(BaseModel):
    """What the model is told about a file cut down to fit: how much of the file it got and, where it can run code,
    that a figure over the whole file is computed there.

    Without a count, models summed the sections they were shown and answered with that as the file's total; with code
    on, some asked the user whether to run it instead of running it.
    """

    section_counts: dict[str, int] = {}
    code_sandbox_offered: bool = False

    def of(self, event: AttachedFileEvent, mode: FitMode, kept: int, t: LocaleHandler) -> str:
        """The note for one file, empty unless it reached the model as excerpts or as its beginning."""
        total = max(self.section_counts.get(event.file_id, kept), kept)
        match mode:
            case FitMode.EXCERPTS:
                fit = t("agent.attached_files.prompt.excerpted", filename=event.filename, kept=kept, total=total)
            case FitMode.BEGINNING:
                fit = t("agent.attached_files.prompt.truncated", filename=event.filename, kept=kept, total=total)
            case _:
                return ""
        pages = (
            t("agent.attached_files.prompt.page_count", pages=event.number_of_pages) if event.number_of_pages else ""
        )
        code = (
            t("agent.attached_files.prompt.whole_file_in_code", filename=event.filename)
            if self.code_sandbox_offered
            else ""
        )
        return " ".join(part for part in (fit, pages, code) if part)
