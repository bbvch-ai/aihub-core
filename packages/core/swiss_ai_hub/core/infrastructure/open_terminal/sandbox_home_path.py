import posixpath

from swiss_ai_hub.core.infrastructure.open_terminal.open_terminal_error import OpenTerminalError


class SandboxHomePath:
    """Paths inside a user's sandbox home, relative to it, whatever the sandbox would accept beyond it.

    The sandbox's file API resolves absolute paths and `..` outside the home, so every caller turns user and model
    paths into home-relative ones here first.
    """

    @staticmethod
    def of(path: str, base: str = ".") -> str:
        """The path relative to the home: `~/…` from the home, anything else from `base`, itself relative to it."""
        if "\0" in path:
            raise OpenTerminalError("A path must not contain NUL characters.")
        if path == "~" or path.startswith("~/"):
            relative = posixpath.normpath(path.removeprefix("~").removeprefix("/") or ".")
        elif path.startswith("/"):
            raise OpenTerminalError(
                f"{path} is an absolute path; use a path inside the home, e.g. ~/{path.lstrip('/')}."
            )
        else:
            relative = posixpath.normpath(posixpath.join(base, path))
        if relative == ".." or relative.startswith("../"):
            raise OpenTerminalError(f"{path} lies outside the home.")
        return relative

    @staticmethod
    def name(name: str) -> str:
        """A single file or folder name, as given for an upload, a new folder or a rename."""
        if not name or name in (".", "..") or "/" in name or "\0" in name:
            raise OpenTerminalError(f"{name!r} is not a valid file or folder name.")
        return name
