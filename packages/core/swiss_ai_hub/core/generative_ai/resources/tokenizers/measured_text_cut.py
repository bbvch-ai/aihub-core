from collections.abc import Callable


class MeasuredTextCut:
    """
    Cuts text to a token limit by binary search over character positions, never by decoding token ids: a
    tokenizer's normalisation (NFKC, collapsed whitespace) would hand back text that differs from the input.

    Safety does not rest on token counts of prefixes or suffixes being monotonic -- under BPE they are not
    ("unbelievable" measures [3, 3, 2, 3, ...]). It rests on the result only ever being a cut that measured as
    fitting, never one inferred to fit. Non-monotonicity costs optimality alone: a slightly longer cut may also
    have fit.
    """

    @staticmethod
    def longest_fitting_tail(text: str, limit: int, count: Callable[[str], int]) -> str:
        low, high = 0, len(text)
        while low < high:
            middle = (low + high) // 2
            if count(text[middle:]) <= limit:
                high = middle
            else:
                low = middle + 1
        return text[low:] or text[-1:]

    @staticmethod
    def longest_fitting_head(text: str, limit: int, count: Callable[[str], int]) -> str:
        """At least one character, so a caller cutting a text into pieces always makes progress."""
        low, high, fitting = 1, len(text), 1
        while low <= high:
            middle = (low + high) // 2
            if count(text[:middle]) <= limit:
                fitting, low = middle, middle + 1
            else:
                high = middle - 1
        return text[:fitting]

    @staticmethod
    def pieces(text: str, limit: int, count: Callable[[str], int]) -> list[str]:
        """The text as consecutive heads, each measured within the limit."""
        pieces: list[str] = []
        rest = text
        while rest:
            head = MeasuredTextCut.longest_fitting_head(rest, limit, count)
            pieces.append(head)
            rest = rest[len(head) :]
        return pieces
