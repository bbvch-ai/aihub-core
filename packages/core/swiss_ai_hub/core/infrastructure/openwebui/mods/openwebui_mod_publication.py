import ast
import hashlib
import json
import sys
from io import BytesIO
from typing import Self
from zipfile import BadZipFile, ZipFile
from zlib import error as CompressionError

from pydantic import BaseModel, JsonValue

from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_compatibility import OpenWebuiModCompatibility
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_package import OpenWebuiModPackage
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_publication_manifest import (
    OpenWebuiModPublicationManifest,
)


class OpenWebuiModPublication(BaseModel):
    revision: str
    manifest: OpenWebuiModPublicationManifest
    files: dict[str, bytes]

    @classmethod
    def from_zip(cls, content: bytes) -> Self:
        if len(content) > OpenWebuiModPackage.MAX_ARCHIVE_BYTES:
            raise ValueError("Publication archive exceeds the 16 MiB upload limit")
        try:
            with ZipFile(BytesIO(content)) as archive:
                files = OpenWebuiModPackage.read_files(archive, max_entries=4 * OpenWebuiModPackage.MAX_ENTRIES + 1)
        except (BadZipFile, CompressionError) as error:
            raise ValueError("Invalid publication ZIP archive") from error
        metadata = files.pop("publication.json", None)
        if metadata is None or len(metadata) > OpenWebuiModPackage.MAX_MANIFEST_BYTES:
            raise ValueError("Publication archive needs a root publication.json of at most 64 KiB")
        manifest = OpenWebuiModPublicationManifest.model_validate(
            json.loads(metadata.decode("utf-8"), object_pairs_hook=OpenWebuiModPackage.unique_json_keys)
        )
        if any(not path.startswith("files/") for path in files):
            raise ValueError("Published browser files must be under files/ in the archive")
        return cls(
            revision=hashlib.sha256(content).hexdigest(),
            manifest=manifest,
            files={path.removeprefix("files/"): data for path, data in files.items()},
        )

    def validate_for_host(
        self, source: OpenWebuiModPackage, compatibility: OpenWebuiModCompatibility, components: set[str],
        callables: dict[str, dict[str, JsonValue]] | None = None,
    ) -> None:
        if self.manifest.source_revision != source.revision:
            raise ValueError("Publication does not match the uploaded source revision")
        if self.manifest.compatibility != compatibility:
            raise ValueError("Publication was compiled for a different Open WebUI host; recompile its source")
        expected_frontend = f"frontend/{source.manifest.frontend}.mjs" if source.manifest.frontend else None
        expected_bootstrap = f"bootstrap/{source.manifest.bootstrap}.mjs" if source.manifest.bootstrap else None
        expected_replacements = {target: f"frontend/{path}.mjs" for target, path in source.manifest.replacements.items()}
        if (
            self.manifest.bootstrap != expected_bootstrap
            or self.manifest.frontend != expected_frontend
            or self.manifest.replacements != expected_replacements
        ):
            raise ValueError("Published entry points do not match the source manifest")
        missing_targets = set(expected_replacements) - components
        if missing_targets:
            raise ValueError(f"Replacement targets are absent from this Open WebUI host: {sorted(missing_targets)}")
        for entry in [expected_bootstrap, expected_frontend, *expected_replacements.values()]:
            if entry is not None and entry not in self.files:
                raise ValueError(f"Published entry file is missing: {entry}")
        self._validate_files(source)
        self._validate_backend(source, compatibility.python)
        self._validate_targets(source, callables or {})

    def _validate_targets(self, source: OpenWebuiModPackage, callables: dict[str, dict[str, JsonValue]]) -> None:
        targets = source.manifest.backend_overrides.keys()
        missing = targets - callables.keys()
        if missing:
            raise ValueError(f"Backend callable targets are absent from this Open WebUI host: {sorted(missing)}")
        expected = {target: callables[target] for target in targets}
        published = self.manifest.backend_targets
        if published != expected:
            changed = sorted(
                target for target in published.keys() | expected.keys() if published.get(target) != expected.get(target)
            )
            raise ValueError(
                f"Backend callable source does not match the running host: {', '.join(changed)}. Recompile the mod."
            )

    def _validate_files(self, source: OpenWebuiModPackage) -> None:
        if not (source.manifest.bootstrap or source.manifest.frontend or source.manifest.replacements) and self.files:
            raise ValueError("A backend-only mod cannot publish browser files")
        for path, content in self.files.items():
            if path.endswith(".mjs"):
                try:
                    content.decode("utf-8")
                except UnicodeDecodeError as error:
                    raise ValueError(f"Published module must be UTF-8: {path}") from error
            else:
                entry, _, original = path.partition("/")
                if (
                    entry not in {"bootstrap", "frontend"}
                    or original.endswith(".py")
                    or original == "mod.json"
                    or source.files.get(original) != content
                ):
                    raise ValueError(f"Published asset must match a non-Python file from the source archive: {path}")

    @staticmethod
    def _validate_backend(source: OpenWebuiModPackage, python_version: str) -> None:
        if source.manifest.backend is None:
            return
        major, minor = (int(part) for part in python_version.split("."))
        version = (major, minor)
        if version > sys.version_info[:2]:
            raise ValueError(f"Backend syntax validation needs Python {python_version} or newer on AI Hub")
        for path, content in source.files.items():
            if not path.endswith(".py"):
                continue
            try:
                syntax = ast.parse(content, filename=path, feature_version=version)
                compile(syntax, path, "exec")
            except (SyntaxError, ValueError) as error:
                raise ValueError(f"Backend source is invalid for Python {python_version}: {path}: {error}") from error
