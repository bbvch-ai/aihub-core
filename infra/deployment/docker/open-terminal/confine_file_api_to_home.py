"""Confine open-terminal's file API to the requesting user's own home in multi-user mode.

Upstream checks the path as written, so a symlink in a user's home pointing into another home, and any path outside
/home such as /proc/1/environ with the API key, pass the check and are then opened with the server's rights, which
reach every home. The patched check resolves links and requires the real path to lie inside the user's home; shell
commands, which run as the user, still see the rest of the system under normal permissions.

Fails the build when the upstream code it replaces changed, so a base-image bump cannot silently drop it.
"""

import pathlib
import sys

import open_terminal.utils.fs as fs_module

ORIGINAL_CHECK = '''    def is_path_allowed(self, path: str) -> bool:
        """Return *False* if *path* is inside another user's home directory."""
        if not self.username:
            return True
        resolved = os.path.abspath(path)
        if not resolved.startswith("/home/"):
            return True
        parts = resolved.split("/")  # ['', 'home', '<user>', ...]
        if len(parts) >= 3:
            target_user_dir = parts[2]
            own_home_name = os.path.basename(self.home)
            if target_user_dir != own_home_name:
                return False
        return True
'''

CONFINED_CHECK = '''    def is_path_allowed(self, path: str) -> bool:
        """Return *False* unless *path*, links resolved, lies inside the user's own home."""
        if not self.username:
            return True
        home = os.path.realpath(self.home)
        resolved = os.path.realpath(path)
        return resolved == home or resolved.startswith(home + os.sep)
'''

ORIGINAL_MESSAGE = 'f"Access denied: {os.path.abspath(path)} belongs to another user"'
CONFINED_MESSAGE = 'f"Access denied: {os.path.abspath(path)} is outside your home"'

# Search and glob reach files without going through UserFS: grep opens a file root directly, glob checks its root and
# stats the files it walks without asking whether they are the user's. Each root is checked first, and glob skips any
# walked entry outside the home.
ORIGINAL_GREP_ROOT = """    target = fs.resolve_path(path, cwd=session_cwd)
    if not await aiofiles.os.path.exists(target):
        raise HTTPException(status_code=404, detail="Search path not found")
"""
CONFINED_GREP_ROOT = """    target = fs.resolve_path(path, cwd=session_cwd)
    fs._check_path(target)
    if not await aiofiles.os.path.exists(target):
        raise HTTPException(status_code=404, detail="Search path not found")
"""
ORIGINAL_GLOB_ROOT = """    target = fs.resolve_path(path, cwd=session_cwd)
    if not await aiofiles.os.path.isdir(target):
        raise HTTPException(status_code=404, detail="Search directory not found")
"""
CONFINED_GLOB_ROOT = """    target = fs.resolve_path(path, cwd=session_cwd)
    fs._check_path(target)
    if not await aiofiles.os.path.isdir(target):
        raise HTTPException(status_code=404, detail="Search directory not found")
"""
ORIGINAL_GLOB_ENTRY = """                full_path = os.path.join(dirpath, name)
                rel_path = os.path.relpath(full_path, target)
"""
CONFINED_GLOB_ENTRY = """                full_path = os.path.join(dirpath, name)
                if not fs.is_path_allowed(full_path):
                    continue
                rel_path = os.path.relpath(full_path, target)
"""


def patch(source_file: pathlib.Path, replacements: list[tuple[str, str]]) -> None:
    source = source_file.read_text()
    for original, _ in replacements:
        if source.count(original) != 1:
            sys.exit(f"open-terminal changed {source_file}; re-check the home confinement patch against it")
    for original, confined in replacements:
        source = source.replace(original, confined)
    source_file.write_text(source)
    print(f"Confined the file API to the user's home in {source_file}")


package = pathlib.Path(fs_module.__file__).parent.parent
patch(pathlib.Path(fs_module.__file__), [(ORIGINAL_CHECK, CONFINED_CHECK), (ORIGINAL_MESSAGE, CONFINED_MESSAGE)])
patch(
    package / "main.py",
    [
        (ORIGINAL_GREP_ROOT, CONFINED_GREP_ROOT),
        (ORIGINAL_GLOB_ROOT, CONFINED_GLOB_ROOT),
        (ORIGINAL_GLOB_ENTRY, CONFINED_GLOB_ENTRY),
    ],
)
