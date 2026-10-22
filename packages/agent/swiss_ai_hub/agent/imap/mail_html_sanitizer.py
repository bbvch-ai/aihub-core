import html
import re

import nh3

# Outlook renders HTML with Word's engine, which ignores `<mark>`; an inline background is what it shows as highlight.
HIGHLIGHT_STYLE = "background-color:#ffff00"

_CONTENT_DROPPING_TAGS = {"script", "style", "title", "head"}

_REPLY_TAGS = {
    "p", "br", "strong", "b", "em", "i", "u", "s", "ul", "ol", "li", "blockquote", "h1", "h2", "h3", "h4",
    "a", "span", "mark", "code", "pre", "hr", "table", "thead", "tbody", "tr", "th", "td",
}  # fmt: skip
_REPLY_ATTRIBUTES = {"a": {"href"}, "span": {"style"}, "th": {"align"}, "td": {"align"}}
_REPLY_STYLE_PROPERTIES = {"background-color", "color", "font-weight", "font-style", "text-decoration"}

# The quoted original keeps its layout (tables, fonts, inline styles) but never an image: a remote one is a tracking
# pixel fetched when the reviewer opens the draft, and an inline `cid:` one points at a part the draft does not carry.
_ORIGINAL_TAGS = _REPLY_TAGS | {"div", "font", "center", "small", "sup", "sub", "h5", "h6", "tfoot", "caption", "col",
                                "colgroup", "dl", "dt", "dd"}  # fmt: skip
_ORIGINAL_ATTRIBUTES = {
    "*": {"style", "align", "dir"},
    "a": {"href"},
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
_BLOCK_BOUNDARY = re.compile(r"(?i)<br\s*/?>|</(?:p|div|tr|li|h[1-6]|table|blockquote|pre)\s*>")
_EXCESS_BLANK_LINES = re.compile(r"\n{3,}")


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
        """Readable plain text of an HTML fragment, line breaks kept at block boundaries."""
        with_breaks = _BLOCK_BOUNDARY.sub(lambda match: f"{match.group(0)}\n", any_html)
        text = html.unescape(nh3.clean(with_breaks, tags=set(), clean_content_tags=_CONTENT_DROPPING_TAGS))
        lines = [line.rstrip() for line in text.splitlines()]
        return _EXCESS_BLANK_LINES.sub("\n\n", "\n".join(lines)).strip()
