import re
from typing import Annotated

from swiss_ai_hub.core.generative_ai import InvalidPathPatternError, KnowledgeDocumentCriteria, KnowledgeDocumentListing

_SEPARATORS = re.compile(r"[,;]")
_YEAR = re.compile(r"(?:19|20)\d{2}")
_GLOB_CHARACTERS = {"*": "[*]", "?": "[?]", "[": "[[]"}


class WrittenLocation:
    """The documents a location the user typed into the request form names, matched against the paths in scope.

    A typed location is a folder, a file, a year or a pattern, several separated by commas. Only what the paths in scope
    hold is taken as a place: a word that names no folder, file or year there may be what the documents say, so it is
    never turned into a pattern that would quietly match nothing or everything.
    """

    @staticmethod
    def criteria(
        text: Annotated[str, "The location as the user typed it"],
        listing: Annotated[KnowledgeDocumentListing, "The documents in scope"],
    ) -> list[KnowledgeDocumentCriteria] | None:
        """One entry per place named; None when any part names no place in scope."""
        pieces = [piece.strip().strip("/") for piece in _SEPARATORS.split(text)]
        found = [WrittenLocation._place(piece, listing) for piece in pieces if piece]
        if not found or any(place is None for place in found):
            return None
        return [criteria for place in found if place for criteria in place]

    @staticmethod
    def _place(piece: str, listing: KnowledgeDocumentListing) -> list[KnowledgeDocumentCriteria] | None:
        if any(character in piece for character in "*?["):
            glob = WrittenLocation._pattern(piece, listing)
            return [KnowledgeDocumentCriteria(path_glob=glob)] if glob else None
        paths = [document.path for document in listing.documents]
        if _YEAR.fullmatch(piece):
            year = rf"(?<!\d){piece}(?!\d)"
            return (
                [KnowledgeDocumentCriteria(path_regex=year)] if any(re.search(year, path) for path in paths) else None
            )
        globs = WrittenLocation._folders(piece, paths) or WrittenLocation._files(piece, paths)
        return [KnowledgeDocumentCriteria(path_glob=glob) for glob in globs] or None

    @staticmethod
    def _pattern(piece: str, listing: KnowledgeDocumentListing) -> str | None:
        """The pattern as written, or anywhere in scope when only that matches; None when nothing in scope matches,
        which also keeps a question mark in plain words from being taken for a pattern."""
        for glob in dict.fromkeys([piece, f"**/{piece}"]):
            try:
                if listing.matching_glob(glob).documents:
                    return glob
            except InvalidPathPatternError:
                return None
        return None

    @staticmethod
    def _folders(piece: str, paths: list[str]) -> list[str]:
        """The folders whose path, or end of path, the piece is; a whole path wins over ends found in other places."""
        folders = dict.fromkeys(
            "/".join(parts[:end]) for parts in (path.split("/") for path in paths) for end in range(1, len(parts))
        )
        wanted = piece.casefold()
        whole = [folder for folder in folders if folder.casefold() == wanted]
        named = whole or [folder for folder in folders if folder.casefold().endswith(f"/{wanted}")]
        return [f"{WrittenLocation._literal(folder)}/**" for folder in named]

    @staticmethod
    def _files(piece: str, paths: list[str]) -> list[str]:
        """The files whose path, end of path, or name without its extension the piece is."""
        wanted = piece.casefold()
        segments = piece.count("/") + 1
        globs: list[str] = []
        for path in paths:
            folded = path.casefold()
            name = path.rsplit("/", 1)[-1]
            if folded == wanted:
                globs.append(WrittenLocation._literal(path))
            elif folded.endswith(f"/{wanted}"):
                globs.append(f"**/{WrittenLocation._literal('/'.join(path.split('/')[-segments:]))}")
            elif name.casefold().rpartition(".")[0] == wanted:
                globs.append(f"**/{WrittenLocation._literal(name)}")
        return list(dict.fromkeys(globs))

    @staticmethod
    def _literal(text: str) -> str:
        return "".join(_GLOB_CHARACTERS.get(character, character) for character in text)
