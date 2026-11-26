import re
from typing import Annotated, ClassVar


class MineruInlineLatex:
    """Turns the inline LaTeX MinerU writes for ordinary text back into that text.

    MinerU sets superscripts, units and some words in math mode: `$1^{\\text{er}}$` for "1er", `$1^{\\circ}$` for "1°",
    `$52^{\\mathrm{bis}}$` for "52bis", `$\\mathrm{CO}_{2}$` for "CO2", `$50\\%$` for "50%". Left as LaTeX, an exact
    search for "1er janvier 2003" or "Art. 52bis" misses the document, and a value the classifier copies as plain text
    is not found in it. A fragment is rewritten only when it becomes plain text with no LaTeX left; a formula such as
    `$a^2 + b^2 = c^2$` keeps its LaTeX, since it has no plain form.
    """

    # Opening and closing `$` hug the content, as MinerU writes it; "$ 9.35 and $ 12" in running text never pairs.
    _INLINE: ClassVar[re.Pattern[str]] = re.compile(r"(?<![$\\])\$(?![$\s])([^$\n]{1,80}?)(?<![\s\\])\$(?!\$)")
    _MARKUP: ClassVar[re.Pattern[str]] = re.compile(r"[\\^_]")
    _MATH: ClassVar[re.Pattern[str]] = re.compile(
        r"[=+<>|]|\\(?:sqrt|frac|sum|prod|int|lim|infty|neq|leq|geq|le|ge|approx|pm|mp|times|div|to|mapsto|"
        r"alpha|beta|gamma|delta|epsilon|lambda|mu|pi|sigma|theta|omega|Delta|Sigma|Omega|left|right|begin|end)\b"
    )
    # A lone letter carrying an index or exponent is a variable ("a^2", "D_{x}"); a word or number carrying one is text.
    _VARIABLE: ClassVar[re.Pattern[str]] = re.compile(r"(?<![A-Za-z\\{])[A-Za-z]\s*[\^_]")
    # The French and Italian "n°" / "nos" is the one lone letter with a superscript that is text.
    _NUMERO: ClassVar[re.Pattern[str]] = re.compile(
        r"\s*(?:\\mathsf\{)?([nN])\}?\s*\^\s*\{?\s*(?:\\(?:mathrm|text)\{)?\s*(o|os|0|\\circ)\s*\}?\s*\}?\s*"
    )
    # A superscript or subscript is text only when it is a word or a number; "4/12" or "x+1" is math.
    _SCRIPT_TEXT: ClassVar[re.Pattern[str]] = re.compile(r"[^\W_]+|-?\d+|°")
    _WRAPPER: ClassVar[re.Pattern[str]] = re.compile(
        r"\\(?:text|mathrm|mathsf|mathbf|mathit|textit|textbf|operatorname)\s*\{([^{}]*)\}"
    )
    _SYMBOLS: ClassVar[dict[str, str]] = {
        r"\circ": "°",
        r"\%": "%",
        r"\&": "&",
        r"\#": "#",
        r"\cdot": "·",
        r"\bullet": "•",
        r"\rightarrow": "→",
        r"\leftarrow": "←",
        r"\Rightarrow": "⇒",
        r"\triangleright": "▸",
        r"\checkmark": "✓",
        r"\square": "□",
        r"\boxtimes": "☒",
        r"\ldots": "…",
        r"\dots": "…",
        r"\,": " ",
        r"\;": " ",
        r"\ ": " ",
        "~": " ",
    }
    _SCRIPT: ClassVar[re.Pattern[str]] = re.compile(r"[\^_]\s*(?:\{([^{}]*)\}|(\S))")
    _SUPERSCRIPT_DIGITS: ClassVar[dict[int, str]] = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
    _SIGNED_NUMBER: ClassVar[re.Pattern[str]] = re.compile(r"-?\d+")
    _GLUED_SUPERSCRIPT: ClassVar[re.Pattern[str]] = re.compile(r"(?<=\w)([⁰¹²³⁴⁵⁶⁷⁸⁹⁻]+)")

    @classmethod
    def as_text(cls, markdown: Annotated[str, "Markdown that may hold MinerU's inline LaTeX"]) -> str:
        if "$" not in markdown:
            return markdown
        return cls._INLINE.sub(lambda match: cls._plain(match[1]) or match[0], markdown)

    @classmethod
    def as_comparable_text(cls, text: Annotated[str, "Text about to be compared after NFKC normalisation"]) -> str:
        """`as_text`, with a superscript number set apart from the word or number it follows.

        NFKC turns "¹" back into "1", so a footnote mark would read as part of what precedes it: "Urteil¹" as "Urteil1",
        "2003¹" as "20031". Apart, "Urteil" stays a whole word and "2003" a year.
        """
        return cls._GLUED_SUPERSCRIPT.sub(r" \1", cls.as_text(text))

    @classmethod
    def _plain(cls, latex: str) -> str | None:
        """The fragment as plain text, or None when it is math or keeps LaTeX that has no plain form."""
        if numero := cls._NUMERO.fullmatch(latex):
            return f"{numero[1]}os" if numero[2] == "os" else f"{numero[1]}°"
        if not cls._MARKUP.search(latex) or cls._MATH.search(latex) or cls._VARIABLE.search(latex):
            return None
        text = latex
        while (unwrapped := cls._WRAPPER.sub(r"\1", text)) != text:
            text = unwrapped
        for command, symbol in cls._SYMBOLS.items():
            text = text.replace(command, symbol)
        scripts = [(match[1] if match[1] is not None else match[2]).strip() for match in cls._SCRIPT.finditer(text)]
        if not all(cls._SCRIPT_TEXT.fullmatch(content) for content in scripts):
            return None
        text = cls._SCRIPT.sub(cls._unscripted, text)
        text = re.sub(r"[{}]", "", text)
        if "\\" in text or "^" in text or "_" in text:
            return None
        return re.sub(r" {2,}", " ", text).strip()

    @classmethod
    def _unscripted(cls, match: re.Match[str]) -> str:
        """A superscript or subscript written inline: letters and signs as they are ("1er", "52bis", "CO2", "1°"), and a
        superscript number as superscript digits ("m²", "10⁶", a footnote mark "¹"), so it does not read as a digit of
        the number or word before it."""
        content = (match[1] if match[1] is not None else match[2]).strip()
        if match[0].startswith("^") and cls._SIGNED_NUMBER.fullmatch(content):
            return content.translate(cls._SUPERSCRIPT_DIGITS)
        return content
