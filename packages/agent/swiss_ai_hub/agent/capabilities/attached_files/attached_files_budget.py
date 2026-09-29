from collections.abc import Callable

from swiss_ai_hub.agent.imap.token_budget import TokenBudget

# Attached files share the room left after the history and the caller's reservation with the other context blocks
# (memory, later web content), so they never claim all of it.
ATTACHED_FILES_SHARE = 0.8


class AttachedFilesBudget:
    """Splits the room left in the prompt fairly between the attached files.

    The final prompt keeps every system message whole and fails when they do not fit, so the files are sized before
    they get there. Small files are placed first and whatever they leave is shared by the rest, so one large file
    never crowds out several small ones.
    """

    def __init__(self, available_tokens: int, token_counter: Callable[[str], list[int]]) -> None:
        self._budget = TokenBudget(max(int(available_tokens * ATTACHED_FILES_SHARE), 0), token_counter)

    def allocate(self, texts: dict[str, str]) -> dict[str, int | None]:
        """For each text, keyed as given, the room it has to be cut down to, or None when it fits whole."""
        counted = sorted(((key, self._budget.count(text)) for key, text in texts.items()), key=lambda item: item[1])
        rooms: dict[str, int | None] = {}
        remaining = self._budget.remaining
        for index, (key, tokens) in enumerate(counted):
            room = remaining // (len(counted) - index)
            if tokens <= room:
                rooms[key] = None
                remaining -= tokens
            else:
                rooms[key] = room
                remaining -= room
        return rooms

    def trim_head(self, text: str, room: int) -> str:
        """The leading whole sentences of `text` that fit `room`, for when relevant sections cannot be picked."""
        return self._budget.trim_head(text, room)
