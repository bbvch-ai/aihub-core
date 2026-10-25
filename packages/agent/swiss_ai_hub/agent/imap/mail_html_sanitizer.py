import html
import re

import nh3

# Outlook renders HTML with Word's engine, which ignores `<mark>`; an inline background is what it shows as highlight.
HIGHLIGHT_STYLE = "background-color:#ffff00"
# Outlook's own default reply font, so neither the reply nor the quote below it changes typeface in an Outlook thread.
OUTLOOK_FONT_STYLE = "font-family:Aptos,Calibri,Arial,Helvetica,sans-serif;font-size:11pt"

_CONTENT_DROPPING_TAGS = {"script", "style", "title", "head"}

_REPLY_TAGS = {
    "p", "br", "strong", "b", "em", "i", "u", "s", "ul", "ol", "li", "blockquote", "h1", "h2", "h3", "h4",
    "a", "span", "mark", "code", "pre", "hr", "table", "thead", "tbody", "tr", "th", "td",
}  # fmt: skip
# `start` carries a list's first number: without it `3. … 4. …` renumbers from 1, and a paragraph opening with `31.`
# (a date, a year) reads as item 1.
_REPLY_ATTRIBUTES = {"a": {"href"}, "ol": {"start"}, "span": {"style"}, "th": {"align"}, "td": {"align"}}
_REPLY_STYLE_PROPERTIES = {"background-color", "color", "font-weight", "font-style", "text-decoration"}

# The quoted original keeps its layout (tables, fonts, inline styles) but never an image: a remote one is a tracking
# pixel fetched when the reviewer opens the draft, and an inline `cid:` one points at a part the draft does not carry.
_ORIGINAL_TAGS = _REPLY_TAGS | {"div", "font", "center", "small", "sup", "sub", "h5", "h6", "tfoot", "caption", "col",
                                "colgroup", "dl", "dt", "dd"}  # fmt: skip
_ORIGINAL_ATTRIBUTES = {
    "*": {"style", "align", "dir"},
    "a": {"href"},
    "ol": {"start"},
    "font": {"color", "face", "size"},
    "table": {"width", "border", "cellpadding", "cellspacing", "bgcolor"},
    "td": {"width", "valign", "colspan", "rowspan", "bgcolor"},
    "th": {"width", "valign", "colspan", "rowspan", "bgcolor"},
    "col": {"width", "span"},
}
_ORIGINAL_STYLE_PROPERTIES = _REPLY_STYLE_PROPERTIES | {
    "font-family", "font-size", "text-align", "vertical-align", "line-height", "width", "border", "border-top",
    "border-bottom", "border-left", "border-right", "border-collapse", "border-color", "margin", "margin-top",
    "margin-bottom", "margin-left", "margin-right", "padding", "padding-top", "padding-bottom", "padding-left",
    "padding-right",
}  # fmt: skip

_URL_SCHEMES = {"http", "https", "mailto"}
# A source newline right after a boundary is consumed, so a `<br>\n` the renderer wrote is one break, not two, and a
# run of closers (`</li></li>` after a nested list, nested `</div>`s) ends one line rather than several.
_LINE_END = re.compile(r"(?i)(?:<br\s*/?>|(?:\s*</(?:div|tr|li)\s*>)+)\n?")
_PARAGRAPH_END = re.compile(r"(?i)</(?:p|h[1-6]|table|blockquote|pre)\s*>\n?")
_EXCESS_BLANK_LINES = re.compile(r"\n{3,}")
# Matched only on nh3 output, which always writes `<a href="...">` with nothing else on the tag.
_LINK = re.compile(r'<a href="(?P<href>[^"]*)">(?P<label>.*?)</a>', re.DOTALL)
_LIST_TAG = re.compile(r'(?i)<(?P<closing>/?)(?P<tag>ol|ul|li)(?: start="(?P<start>[^"]*)")?>\n?')
_LIST_START = re.compile(r"-?\d+")


class MailHtmlSanitizer:
    """Allowlist sanitising for every piece of HTML that goes into a reply draft.

    Both inputs are untrusted: the quoted original is sender markup, and the reply body is model output steered by that
    same inbound mail. Nothing outside the allowlist survives, so a draft never carries script, forms, event handlers or
    images, whatever the sender or the model wrote.
    """

    @staticmethod
    def reply(rendered_html: str) -> str:
        """The model's rendered reply, reduced to text formatting, with highlights turned into inline backgrounds."""
        cleaned = nh3.clean(
            rendered_html,
            tags=_REPLY_TAGS,
            clean_content_tags=_CONTENT_DROPPING_TAGS,
            attributes=_REPLY_ATTRIBUTES,
            filter_style_properties=_REPLY_STYLE_PROPERTIES,
            url_schemes=_URL_SCHEMES,
        )
        return cleaned.replace("<mark>", f'<span style="{HIGHLIGHT_STYLE}">').replace("</mark>", "</span>")

    @staticmethod
    def original(original_html: str) -> str:
        """The sender's HTML body, keeping its layout but none of its active content or images."""
        return nh3.clean(
            original_html,
            tags=_ORIGINAL_TAGS,
            clean_content_tags=_CONTENT_DROPPING_TAGS,
            attributes=_ORIGINAL_ATTRIBUTES,
            filter_style_properties=_ORIGINAL_STYLE_PROPERTIES,
            url_schemes=_URL_SCHEMES,
        )

    @staticmethod
    def to_text(any_html: str) -> str:
        """Readable plain text of an HTML fragment: line breaks at block boundaries, a dash per list item, and each
        link's target kept next to its text, since stripping the tag would otherwise drop the address with it."""
        normalised = nh3.clean(any_html, tags=_ORIGINAL_TAGS, clean_content_tags=_CONTENT_DROPPING_TAGS,
                               attributes={"a": {"href"}, "ol": {"start"}}, url_schemes=_URL_SCHEMES,
                               link_rel=None)  # fmt: skip
        with_links = _LINK.sub(MailHtmlSanitizer._link_as_text, normalised)
        with_markers = MailHtmlSanitizer._with_list_markers(with_links)
        with_breaks = _PARAGRAPH_END.sub("\n\n", _LINE_END.sub("\n", with_markers))
        text = html.unescape(nh3.clean(with_breaks, tags=set(), clean_content_tags=_CONTENT_DROPPING_TAGS))
        lines = [line.rstrip() for line in text.splitlines()]
        return _EXCESS_BLANK_LINES.sub("\n\n", "\n".join(lines)).strip()

    @staticmethod
    def _with_list_markers(normalised: str) -> str:
        """Prefix each list item with `-` or its number, indented by nesting depth, the way the Markdown read."""
        open_lists: list[list[int]] = []
        return _LIST_TAG.sub(lambda match: MailHtmlSanitizer._list_marker(match, open_lists), normalised)

    @staticmethod
    def _list_marker(match: re.Match[str], open_lists: list[list[int]]) -> str:
        """The text replacing one list tag. `open_lists` holds one entry per open list: empty for a bulleted list,
        the running item number for a numbered one."""
        tag = match.group("tag").lower()
        closing = bool(match.group("closing"))
        if tag == "li":
            return match.group(0) if closing or not open_lists else MailHtmlSanitizer._item_prefix(open_lists)
        if closing:
            if open_lists:
                open_lists.pop()
            return "" if open_lists else "\n\n"
        open_lists.append([MailHtmlSanitizer._list_start(match.group("start")) - 1] if tag == "ol" else [])
        return ""

    @staticmethod
    def _list_start(start: str | None) -> int:
        """The first item's number. A missing or non-numeric `start` counts from 1, as a browser does."""
        return int(start) if start and _LIST_START.fullmatch(start) else 1

    @staticmethod
    def _item_prefix(open_lists: list[list[int]]) -> str:
        indent = "   " * (len(open_lists) - 1)
        counter = open_lists[-1]
        if not counter:
            return f"{indent}- "
        counter[0] += 1
        return f"{indent}{counter[0]}. "

    @staticmethod
    def _link_as_text(match: re.Match[str]) -> str:
        """`text <target>`, or the bare target when the text already is it (an autolinked URL, a `www.` address
        given its `https://`, or an e-mail address).

        The brackets go in escaped, so the final tag strip keeps them as text."""
        target = html.unescape(match.group("href")).removeprefix("mailto:")
        label = match.group("label")
        if html.unescape(nh3.clean(label, tags=set())).strip() in (target, target.removeprefix("https://")):
            return label
        return f"{label} &lt;{html.escape(target)}&gt;"
