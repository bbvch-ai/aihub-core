import hashlib
from io import BytesIO
from pathlib import PurePosixPath
from zipfile import BadZipFile, ZipFile

from fastapi import HTTPException


class FrontendArchive:
    def __init__(self, revision: str, content: bytes) -> None:
        if hashlib.sha256(content).hexdigest() != revision:
            raise HTTPException(502, "Published mod archive failed its integrity check.")
        # The publishing API validates the archive format. Keep expansion bounded here too.
        try:
            with ZipFile(BytesIO(content)) as archive:
                entries = archive.infolist()
                if len(entries) > 1025 or sum(entry.file_size for entry in entries) > 32 * 1024 * 1024:
                    raise HTTPException(502, "Published mod archive exceeds the expansion limit.")
                if "publication.json" not in archive.namelist():
                    raise HTTPException(502, "Published mod archive has no manifest.")
        except BadZipFile as error:
            raise HTTPException(502, "Invalid published mod archive.") from error
        self.content = content

    def read(self, filename: str, *, manifest: bool = False) -> bytes:
        path = PurePosixPath(filename)
        if path.is_absolute() or path.as_posix() != filename or any(part in {".", ".."} for part in path.parts):
            raise HTTPException(404, "Mod file not found.")
        member = "publication.json" if manifest else f"files/{filename}"
        with ZipFile(BytesIO(self.content)) as archive:
            try:
                return archive.read(member)
            except KeyError as error:
                raise HTTPException(404, "Mod file not found.") from error
