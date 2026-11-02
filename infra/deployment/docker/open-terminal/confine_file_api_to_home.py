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

    def is_node_in_home(self, path: str) -> bool:
        """Return *True* when *path*'s own location — its parent, not its link target — is in the home.

        Operations that act on the directory entry itself (listing, deleting, moving) use this so a user's own
        link that points outside their home stays visible and removable; reads *through* such a link are still
        blocked by is_path_allowed, which resolves the target.
        """
        if not self.username:
            return True
        home = os.path.realpath(self.home)
        parent = os.path.realpath(os.path.dirname(os.path.abspath(path)))
        return parent == home or parent.startswith(home + os.sep)

    def _check_node(self, path: str) -> None:
        """Reject a path whose own location — its parent, not its link target — is outside the home."""
        if not self.is_node_in_home(path):
            raise PermissionError(f"Access denied: {os.path.abspath(path)} is outside your home")
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

# delete and move act on the entry itself, so the endpoints check its location without following it: a link in the
# home that points outside it is removable and movable, while its target is left untouched. The existence and type
# pre-checks use lstat semantics (lexists / islink) so they do not resolve the link and 403 before remove/move run.
ORIGINAL_DELETE_BODY = """    target = fs.resolve_path(path)
    if not await fs.exists(target):
        raise HTTPException(status_code=404, detail="Path not found")
    is_dir = await fs.isdir(target)
"""
CONFINED_DELETE_BODY = """    target = fs.resolve_path(path)
    fs._check_node(target)
    if not os.path.lexists(target):
        raise HTTPException(status_code=404, detail="Path not found")
    is_dir = not os.path.islink(target) and os.path.isdir(target)
"""
ORIGINAL_MOVE_BODY = """    if not await fs.exists(source):
        raise HTTPException(status_code=404, detail="Source path not found")

    dest_parent = os.path.dirname(destination)
    if not await fs.isdir(dest_parent):
        raise HTTPException(status_code=400, detail="Destination parent directory not found")

    if await fs.exists(destination):
        raise HTTPException(status_code=409, detail="Destination already exists")
"""
CONFINED_MOVE_BODY = """    fs._check_node(source)
    if not os.path.lexists(source):
        raise HTTPException(status_code=404, detail="Source path not found")

    dest_parent = os.path.dirname(destination)
    if not await fs.isdir(dest_parent):
        raise HTTPException(status_code=400, detail="Destination parent directory not found")

    if os.path.lexists(destination):
        raise HTTPException(status_code=409, detail="Destination already exists")
"""

# Listing, deleting and moving act on the directory entry itself, so they are checked by location, not by link
# target — otherwise a user's own link pointing outside their home (e.g. a venv's python) would vanish from the
# browser and refuse to delete. The entry is never followed: listdir reports the link's own stat, remove unlinks
# it instead of recursing into its target, and move leaves its target untouched and skips the ownership fixup.
ORIGINAL_LISTDIR_ENTRY = """            for name in sorted(os.listdir(path)):
                full = os.path.join(path, name)
                if not self.is_path_allowed(full):
                    continue
                try:
                    s = os.stat(full)
                    entries.append({
                        "name": name,
                        "type": "directory" if os.path.isdir(full) else "file",
                        "size": s.st_size,
                        "modified": s.st_mtime,
                    })
                except OSError:
                    continue
"""
CONFINED_LISTDIR_ENTRY = """            for name in sorted(os.listdir(path)):
                full = os.path.join(path, name)
                if not self.is_node_in_home(full):
                    continue
                try:
                    s = os.stat(full, follow_symlinks=False)
                    is_dir = not os.path.islink(full) and os.path.isdir(full)
                    entries.append({
                        "name": name,
                        "type": "directory" if is_dir else "file",
                        "size": s.st_size,
                        "modified": s.st_mtime,
                    })
                except OSError:
                    continue
"""

ORIGINAL_REMOVE = '''    async def remove(self, path: str) -> None:
        """Remove *path* (file or directory)."""
        self._check_path(path)
        if os.path.isdir(path):
            await asyncio.to_thread(shutil.rmtree, path)
        else:
            await aiofiles.os.remove(path)
'''
CONFINED_REMOVE = '''    async def remove(self, path: str) -> None:
        """Remove *path* (file or directory).

        Checked by location so a link in the home that points outside it can be deleted; a link is unlinked
        rather than followed, so its target is never recursed into or removed.
        """
        if not self.is_node_in_home(path):
            raise PermissionError(f"Access denied: {os.path.abspath(path)} is outside your home")
        if os.path.islink(path) or not os.path.isdir(path):
            await aiofiles.os.remove(path)
        else:
            await asyncio.to_thread(shutil.rmtree, path)
'''

ORIGINAL_MOVE = '''    async def move(self, source: str, destination: str) -> None:
        """Move *source* to *destination*."""
        self._check_path(source)
        self._check_path(destination)
        await asyncio.to_thread(shutil.move, source, destination)
        await self._chown(destination)
'''
CONFINED_MOVE = '''    async def move(self, source: str, destination: str) -> None:
        """Move *source* to *destination*.

        Both ends are checked by location, so a link pointing outside the home can be renamed within it; the
        link node moves and its target is untouched. The ownership fixup is skipped for a link so it is not
        followed to chown the target.
        """
        if not self.is_node_in_home(source):
            raise PermissionError(f"Access denied: {os.path.abspath(source)} is outside your home")
        if not self.is_node_in_home(destination):
            raise PermissionError(f"Access denied: {os.path.abspath(destination)} is outside your home")
        await asyncio.to_thread(shutil.move, source, destination)
        if not os.path.islink(destination):
            await self._chown(destination)
'''


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
patch(
    pathlib.Path(fs_module.__file__),
    [
        (ORIGINAL_CHECK, CONFINED_CHECK),
        (ORIGINAL_MESSAGE, CONFINED_MESSAGE),
        (ORIGINAL_LISTDIR_ENTRY, CONFINED_LISTDIR_ENTRY),
        (ORIGINAL_REMOVE, CONFINED_REMOVE),
        (ORIGINAL_MOVE, CONFINED_MOVE),
    ],
)
patch(
    package / "main.py",
    [
        (ORIGINAL_GREP_ROOT, CONFINED_GREP_ROOT),
        (ORIGINAL_GLOB_ROOT, CONFINED_GLOB_ROOT),
        (ORIGINAL_GLOB_ENTRY, CONFINED_GLOB_ENTRY),
        (ORIGINAL_DELETE_BODY, CONFINED_DELETE_BODY),
        (ORIGINAL_MOVE_BODY, CONFINED_MOVE_BODY),
    ],
)
