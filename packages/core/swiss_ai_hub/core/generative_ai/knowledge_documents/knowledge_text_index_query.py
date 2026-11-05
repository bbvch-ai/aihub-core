import unicodedata
from typing import Annotated, Self

from pydantic import BaseModel, Field

# Letters PCRE2's caseless matching treats as one letter while PostgreSQL's `lower()` does not, such as the micro sign
# and Greek mu, or final and medial sigma. A caseless query matches them through the single-character wildcard, so
# the index still returns every document the scan would. `s`, `S`, `i` and `I` stay literal: wildcarding them would
# leave hardly any query a usable trigram, and the only cost is that a document spelling `s` as the long `ſ` is not
# found through the index.
_FOLD_MISMATCHES = frozenset("ıſµΜμͅΙιιΒβϐΕεϵΘθϑϴΚκϰΠπϖΡρϱΣςσΦφϕВвᲀДдᲁОоᲂСсᲃТтᲄᲅЪъᲆѢѣᲇᲈꙊꙋṠṡẛ")
_LIKE_SPECIAL = frozenset("\\%_")
_TRIGRAM = 3


class KnowledgeTextIndexQuery(BaseModel):
    """A literal content search as `LIKE` patterns for the trigram index, or no query when the index cannot help.

    The index only narrows the candidates; FerretDB then applies the scan's own filter to them, so a pattern may match
    more than the scan but never less. Regular expressions are not translated. A pattern needs three word characters
    in a row, from which `pg_trgm` takes a trigram; without one the index would be read whole, and the scan is cheaper.
    """

    patterns: Annotated[list[str], Field(description="`LIKE` patterns, composed and decomposed, any of which matches")]
    case_sensitive: Annotated[bool, Field(description="Whether to compare with `LIKE` rather than `ILIKE`")]

    @classmethod
    def from_query(cls, query: str, is_regex: bool, case_sensitive: bool) -> Self | None:
        if is_regex:
            return None
        composed = unicodedata.normalize("NFC", query)
        variants = dict.fromkeys([composed, unicodedata.normalize("NFD", composed)])
        patterns = [cls._like_pattern(variant, case_sensitive) for variant in variants]
        if not all(cls._has_trigram(pattern) for pattern in patterns):
            return None
        return cls(patterns=patterns, case_sensitive=case_sensitive)

    @staticmethod
    def _like_pattern(text: str, case_sensitive: bool) -> str:
        characters = []
        for character in text:
            if character in _LIKE_SPECIAL:
                characters.append(f"\\{character}")
            elif not case_sensitive and character in _FOLD_MISMATCHES:
                characters.append("_")
            else:
                characters.append(character)
        return f"%{''.join(characters)}%"

    @staticmethod
    def _has_trigram(pattern: str) -> bool:
        run = 0
        for character in pattern:
            run = run + 1 if character.isalnum() else 0
            if run >= _TRIGRAM:
                return True
        return False
