from markdown_it import MarkdownIt
from markdown_it.rules_inline.state_inline import Delimiter, StateInline

_MARKER = "="


class HighlightMarkdownRule:
    """`==text==` as `<mark>`, parsed by markdown-it like any other inline delimiter.

    A parser rule rather than a text substitution, so code spans and autolinks are never touched. It follows the
    strikethrough rule in markdown-it-py with one difference: like `_emphasis_`, it never opens or closes inside a word,
    so `status==active and mode==test` stays text. Only runs of exactly two markers count; `===` is left as written.
    """

    @staticmethod
    def install(markdown: MarkdownIt) -> MarkdownIt:
        markdown.inline.ruler.before("emphasis", "highlight", HighlightMarkdownRule._tokenize)
        markdown.inline.ruler2.before("emphasis", "highlight", HighlightMarkdownRule._post_process)
        return markdown

    @staticmethod
    def _tokenize(state: StateInline, silent: bool) -> bool:
        if silent or state.src[state.pos] != _MARKER:
            return False

        scanned = state.scanDelims(state.pos, False)
        token = state.push("text", "", 0)
        token.content = _MARKER * scanned.length
        if scanned.length == 2:
            state.delimiters.append(
                Delimiter(
                    marker=ord(_MARKER),
                    length=0,
                    token=len(state.tokens) - 1,
                    end=-1,
                    open=scanned.can_open,
                    close=scanned.can_close,
                )
            )
        state.pos += scanned.length
        return True

    @staticmethod
    def _post_process(state: StateInline) -> None:
        HighlightMarkdownRule._pair(state, state.delimiters)
        for meta in state.tokens_meta:
            if meta and "delimiters" in meta:
                HighlightMarkdownRule._pair(state, meta["delimiters"])

    @staticmethod
    def _pair(state: StateInline, delimiters: list[Delimiter]) -> None:
        """Turn each balanced opener/closer pair (matched by markdown-it's `balance_pairs`) into mark tags."""
        for opener in delimiters:
            if opener.marker != ord(_MARKER) or opener.end == -1:
                continue
            for token_index, token_type, nesting in (
                (opener.token, "mark_open", 1),
                (delimiters[opener.end].token, "mark_close", -1),
            ):
                token = state.tokens[token_index]
                token.type = token_type
                token.tag = "mark"
                token.nesting = nesting
                token.markup = _MARKER * 2
                token.content = ""
