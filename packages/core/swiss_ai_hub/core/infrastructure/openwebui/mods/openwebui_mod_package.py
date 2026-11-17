import hashlib
import json
import stat
from io import BytesIO
from pathlib import PurePosixPath
from typing import ClassVar, Self
from zipfile import ZIP_DEFLATED, ZIP_STORED, BadZipFile, ZipFile, ZipInfo
from zlib import error as CompressionError

from pydantic import BaseModel, JsonValue

from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_manifest import OpenWebuiModManifest


class OpenWebuiModPackage(BaseModel):
    """Inspect uploaded source without extracting files, importing modules or running installers."""

    MAX_ARCHIVE_BYTES: ClassVar[int] = 16 * 1024 * 1024
    MAX_EXPANDED_BYTES: ClassVar[int] = 32 * 1024 * 1024
    MAX_ENTRIES: ClassVar[int] = 512
    MAX_MANIFEST_BYTES: ClassVar[int] = 64 * 1024

    revision: str
    manifest: OpenWebuiModManifest
    files: dict[str, bytes]

    @classmethod
    def from_zip(cls, content: bytes) -> Self:
        if len(content) > cls.MAX_ARCHIVE_BYTES:
            raise ValueError("Mod archive exceeds the 16 MiB upload limit")
        try:
            with ZipFile(BytesIO(content)) as archive:
                files = cls.read_files(archive)
        except (BadZipFile, CompressionError) as error:
            raise ValueError("Invalid mod ZIP archive") from error
        manifest = cls.read_manifest(files)
        for path in manifest.entry_paths:
            if path not in files:
                raise ValueError(f"Mod entry file is missing: {path}")
            try:
                files[path].decode("utf-8")
            except UnicodeDecodeError as error:
                raise ValueError(f"Mod entry source must be UTF-8: {path}") from error
        return cls(revision=hashlib.sha256(content).hexdigest(), manifest=manifest, files=files)

    @classmethod
    def read_files(cls, archive: ZipFile, max_entries: int | None = None) -> dict[str, bytes]:
        entries = archive.infolist()
        limit = cls.MAX_ENTRIES if max_entries is None else max_entries
        if len(entries) > limit:
            raise ValueError(f"Mod archive exceeds the {limit} entry limit")
        files: dict[str, bytes] = {}
        names: set[str] = set()
        remaining = cls.MAX_EXPANDED_BYTES
        for entry in entries:
            name = cls.validate_entry(entry)
            if name in names:
                raise ValueError(f"Duplicate mod archive path: {name}")
            names.add(name)
            if entry.is_dir():
                continue
            if entry.file_size > remaining:
                raise ValueError("Expanded mod archive exceeds the 32 MiB limit")
            with archive.open(entry) as source:
                data = source.read(remaining + 1)
            remaining -= len(data)
            if remaining < 0:
                raise ValueError("Expanded mod archive exceeds the 32 MiB limit")
            files[name] = data
        for name in names:
            if any(parent.as_posix() in files for parent in PurePosixPath(name).parents):
                raise ValueError(f"Mod archive path has a file as its parent: {name}")
        return files

    @staticmethod
    def validate_entry(entry: ZipInfo) -> str:
        name = entry.filename.removesuffix("/") if entry.is_dir() else entry.filename
        OpenWebuiModManifest.validate_path(name)
        if entry.orig_filename != entry.filename:
            raise ValueError("Mod archive paths cannot contain null characters")
        mode = stat.S_IFMT(entry.external_attr >> 16)
        expected_mode = stat.S_IFDIR if entry.is_dir() else stat.S_IFREG
        if mode not in {0, expected_mode}:
            raise ValueError(f"Mod archive contains a link or special file: {name}")
        if entry.flag_bits & 1:
            raise ValueError("Encrypted mod archives are not supported")
        if entry.compress_type not in {ZIP_STORED, ZIP_DEFLATED}:
            raise ValueError("Mod archives must use stored or deflated ZIP entries")
        return name

    @classmethod
    def read_manifest(cls, files: dict[str, bytes]) -> OpenWebuiModManifest:
        source = files.get("mod.json")
        if source is None:
            raise ValueError("Mod archive must contain mod.json at its root")
        if len(source) > cls.MAX_MANIFEST_BYTES:
            raise ValueError("mod.json exceeds the 64 KiB limit")
        data = json.loads(source.decode("utf-8"), object_pairs_hook=cls.unique_json_keys)
        return OpenWebuiModManifest.model_validate(data)

    @staticmethod
    def unique_json_keys(pairs: list[tuple[str, JsonValue]]) -> dict[str, JsonValue]:
        result: dict[str, JsonValue] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate manifest key: {key}")
            result[key] = value
        return result
