from collections.abc import Callable

from swiss_ai_hub.agent.imap.token_budget import TokenBudget

# Attached files share the room left after the chat history with the other enrichers (memory, later web
# content), so they never claim all of it.
ATTACHED_FILES_SHARE = 0.8


class AttachedFilesBudget:
    """Splits the room left in the prompt fairly between the attached files, trimming the ones that do not fit.

    The join can only drop whole blocks when the prompt overflows, which would lose a large file entirely, so the
    files are cut down to size before they reach it. Small files are placed first and whatever they leave is shared
    by the rest, so one large file never crowds out several small ones.
    """

    def __init__(self, available_tokens: int, token_counter: Callable[[str], list[int]]) -> None:
        self._budget = TokenBudget(max(int(available_tokens * ATTACHED_FILES_SHARE), 0), token_counter)

    def fit(self, texts: dict[str, str]) -> dict[str, tuple[str, bool]]:
        """Each text as it fits, keyed as given, with whether it had to be trimmed."""
        counted = sorted(
            ((key, text, self._budget.count(text)) for key, text in texts.items()), key=lambda item: item[2]
        )
        fitted: dict[str, tuple[str, bool]] = {}
        remaining = self._budget.remaining
        for index, (key, text, tokens) in enumerate(counted):
            room = remaining // (len(counted) - index)
            if tokens <= room:
                fitted[key] = (text, False)
                remaining -= tokens
            else:
                fitted[key] = (self._budget.trim_head(text, room), True)
                remaining -= room
        return fitted
