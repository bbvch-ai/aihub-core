import re

from linkify_it import LinkifyIt
from linkify_it.main import Match
from markdown_it import MarkdownIt

_WWW = "www."


class LinkifyMarkdownRule:
    """Bare URLs as links: a reply quoting `https://…` or `www.…` from its prompt would otherwise show plain text.

    Only addresses with a scheme, a `www.` prefix or an `@` count. linkify-it's fuzzy matching is off because it also
    takes any word ending in a country code for a domain, so a file named `bericht.py` would become a link.
    A `www.` address is given `https://`, as a browser does with a typed one.
    """

    @staticmethod
    def install(markdown: MarkdownIt) -> MarkdownIt:
        markdown.options["linkify"] = True
        markdown.enable("linkify")
        linkify: LinkifyIt = markdown.linkify
        linkify.set({"fuzzy_link": False})
        linkify.add(
            _WWW,
            {
                "validate": re.compile(f"^{linkify.re['src_host_port_strict']}{linkify.re['src_path']}", re.IGNORECASE),
                "normalize": LinkifyMarkdownRule._with_scheme,
            },
        )
        return markdown

    @staticmethod
    def _with_scheme(_linkify: LinkifyIt, match: Match) -> None:
        match.url = f"https://{match.url}"
