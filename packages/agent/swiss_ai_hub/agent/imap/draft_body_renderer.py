import re

from markdown_it import MarkdownIt

from swiss_ai_hub.agent.imap.mail_html_sanitizer import MailHtmlSanitizer

# `==text==` is the highlight syntax the draft prompt offers. CommonMark has none, so it becomes `<mark>` before
# rendering and the sanitiser turns that into the inline background Outlook understands.
_HIGHLIGHT = re.compile(r"==(?=\S)(.+?)(?<=\S)==")


class DraftBodyRenderer:
    """Turns the Markdown a drafting model writes into the HTML and plain-text parts of a draft.

    Markdown rather than HTML is what the model is asked for: models already write it unprompted (the knowledge agent's
    answers are Markdown), and it reads acceptably as the plain-text alternative. Raw HTML in the output is still
    rendered, because a prompt asking for highlighting often gets a `<span style=...>` back, and the sanitiser decides
    what of it survives.
    """

    _markdown = MarkdownIt("commonmark", {"html": True, "breaks": True}).enable("table")

    @staticmethod
    def html(body: str) -> str:
        """The reply as sanitised HTML."""
        rendered = DraftBodyRenderer._markdown.render(_HIGHLIGHT.sub(r"<mark>\1</mark>", body))
        return MailHtmlSanitizer.reply(rendered)

    @staticmethod
    def text(body: str) -> str:
        """The reply as plain text: the Markdown as written, minus highlight markers and any HTML tags."""
        return MailHtmlSanitizer.to_text(_HIGHLIGHT.sub(r"\1", body).replace("\n", "<br>"))
