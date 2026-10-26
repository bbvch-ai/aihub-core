from markdown_it import MarkdownIt

from swiss_ai_hub.agent.imap.highlight_markdown_rule import HighlightMarkdownRule
from swiss_ai_hub.agent.imap.linkify_markdown_rule import LinkifyMarkdownRule
from swiss_ai_hub.agent.imap.mail_html_sanitizer import MailHtmlSanitizer


class DraftBodyRenderer:
    """Turns the Markdown a drafting model writes into the HTML and plain-text parts of a draft.

    Markdown rather than HTML is what the model is asked for: models already write it unprompted (the knowledge agent's
    answers are Markdown). Raw HTML in the output is escaped, not rendered: replies routinely contain angle brackets
    that are not markup — a `<Ihr Name>` sign-off placeholder, `a<b` in a comparison — and parsing those as tags made
    them vanish or left the rest of the reply bold. `==text==` is the one highlight syntax, handled by the parser, and
    bare URLs become links.
    """

    _markdown = LinkifyMarkdownRule.install(
        HighlightMarkdownRule.install(MarkdownIt("commonmark", {"html": False, "breaks": True}).enable("table"))
    )

    @staticmethod
    def html(body: str) -> str:
        """The reply as sanitised HTML."""
        return MailHtmlSanitizer.reply(DraftBodyRenderer._markdown.render(body))

    @staticmethod
    def text(body: str) -> str:
        """The reply as plain text, derived from the rendered HTML so it reads the way the HTML part does."""
        return MailHtmlSanitizer.to_text(DraftBodyRenderer.html(body))
