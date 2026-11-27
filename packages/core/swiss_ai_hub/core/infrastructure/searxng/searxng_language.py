from enum import StrEnum


class SearxngLanguage(StrEnum):
    """The languages a profile can ask SearXNG's engines for results in, or `auto` to leave it to them."""

    AUTO = "auto"
    DE = "de"
    EN = "en"
    FR = "fr"
    IT = "it"
