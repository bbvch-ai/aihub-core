from enum import StrEnum


class SearxngEngine(StrEnum):
    """The engines this deployment's SearXNG queries (`keep_only` in `infra/configs/searxng/settings.yml`).

    Listed here so an agent profile can narrow a search to some of them; naming an engine SearXNG does not run would
    return nothing.
    """

    BRAVE = "brave"
    DUCKDUCKGO = "duckduckgo"
    MOJEEK = "mojeek"
    QWANT = "qwant"
    STARTPAGE = "startpage"
    WIKIDATA = "wikidata"
    WIKIPEDIA = "wikipedia"
