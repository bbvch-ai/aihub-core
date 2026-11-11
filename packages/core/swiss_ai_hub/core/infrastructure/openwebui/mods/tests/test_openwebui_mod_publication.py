import json
from io import BytesIO
from typing import Any
from zipfile import ZipFile

import pytest

from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_compatibility import OpenWebuiModCompatibility
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_package import OpenWebuiModPackage
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_publication import OpenWebuiModPublication

pytestmark = pytest.mark.unit


class TestOpenWebuiModPublication:
    TARGET = "src/lib/Menu.svelte"
    HOST = OpenWebuiModCompatibility(
        openwebui="0.11.4", source_commit="a" * 40, svelte="5.56.0", host_protocol=1, python="3.11"
    )

    @staticmethod
    def archive(files: dict[str, str | bytes]) -> bytes:
        buffer = BytesIO()
        with ZipFile(buffer, "w") as archive:
            for path, content in files.items():
                archive.writestr(path, content)
        return buffer.getvalue()

    @classmethod
    def source(cls, backend: str = "raise RuntimeError('Never executed')") -> OpenWebuiModPackage:
        return OpenWebuiModPackage.from_zip(cls.archive({
            "mod.json": json.dumps({"format": 1, "id": "tools", "name": "Tools", "version": "1",
                                    "replacements": {cls.TARGET: "Menu.svelte"}, "backend": "backend/mod.py"}),
            "Menu.svelte": "<button>Tools</button>",
            "icon.png": b"\x89PNG",
            "backend/mod.py": backend,
        }))

    @classmethod
    def publication(cls, source: OpenWebuiModPackage, **changes: Any) -> OpenWebuiModPublication:
        metadata = {"format": 1, "source_revision": source.revision, "compatibility": cls.HOST.model_dump(),
                    "frontend": None, "replacements": {cls.TARGET: "frontend/Menu.svelte.mjs"}} | changes
        return OpenWebuiModPublication.from_zip(cls.archive({
            "publication.json": json.dumps(metadata),
            "files/frontend/Menu.svelte.mjs": "export default function Menu() {}",
            "files/frontend/icon.png": b"\x89PNG",
        }))

    def test_full_stack_publication_keeps_backend_private_and_does_not_execute_source(self) -> None:
        source = self.source()
        publication = self.publication(source)
        publication.validate_for_host(source, self.HOST, {self.TARGET})
        assert publication.manifest.source_revision == source.revision
        assert set(publication.files) == {"frontend/Menu.svelte.mjs", "frontend/icon.png"}
        assert len(publication.revision) == 64

    def test_callable_targets_and_changed_source_require_recompilation(self) -> None:
        source = self.source()
        target = 'open_webui.routers.users:get_user_info_by_session_user'
        source.manifest.backend_overrides = {target: 'info'}
        fingerprint = {'source_sha256': 'a' * 64}
        publication = self.publication(source, backend_targets={target: fingerprint})
        publication.validate_for_host(source, self.HOST, {self.TARGET}, {target: fingerprint})
        with pytest.raises(ValueError, match='targets are absent'):
            publication.validate_for_host(source, self.HOST, {self.TARGET}, {})
        with pytest.raises(ValueError, match='source does not match') as caught:
            publication.validate_for_host(source, self.HOST, {self.TARGET}, {target: {'source_sha256': 'b' * 64}})
        assert target in str(caught.value)
        source.manifest.backend_overrides = {}
        with pytest.raises(ValueError, match='source does not match'):
            publication.validate_for_host(source, self.HOST, {self.TARGET}, {target: fingerprint})

    @pytest.mark.parametrize("changes, error", [
        ({"source_revision": "0" * 64}, "source revision"),
        ({"frontend": "other.mjs"}, "entry points"),
        ({"replacements": {}}, "entry points"),
        ({"compatibility": {"openwebui": "0.11.4", "source_commit": "b" * 40, "svelte": "5.56.0",
                            "host_protocol": 1, "python": "3.11"}}, "different Open WebUI host"),
    ])
    def test_rejects_mismatched_source_host_or_entries(self, changes: dict[str, Any], error: str) -> None:
        source = self.source()
        with pytest.raises(ValueError, match=error):
            self.publication(source, **changes).validate_for_host(source, self.HOST, {self.TARGET})

    def test_missing_targets_and_entry_files_fail(self) -> None:
        source = self.source()
        publication = self.publication(source)
        with pytest.raises(ValueError, match="targets are absent"):
            publication.validate_for_host(source, self.HOST, set())
        del publication.files["frontend/Menu.svelte.mjs"]
        with pytest.raises(ValueError, match="entry file is missing"):
            publication.validate_for_host(source, self.HOST, {self.TARGET})

    @pytest.mark.parametrize("path, content", [
        ("backend/mod.py", b"raise RuntimeError()"),
        ("mod.json", b"{}"),
        ("unrelated.png", b"\x89PNG"),
        ("icon.png", b"different bytes"),
        ("bad.mjs", b"\xff"),
    ])
    def test_frontend_output_cannot_smuggle_python_or_change_source_assets(self, path: str, content: bytes) -> None:
        source = self.source()
        publication = self.publication(source)
        publication.files[path if path.startswith("bootstrap/") else f"frontend/{path}"] = content
        with pytest.raises(ValueError, match="asset must match|module must be UTF-8"):
            publication.validate_for_host(source, self.HOST, {self.TARGET})

    @pytest.mark.parametrize("code", ["def broken(:", "type NewAlias = str", "return 1", "break"])
    def test_backend_syntax_uses_the_host_python_version_without_execution(self, code: str) -> None:
        source = self.source(backend=code)
        with pytest.raises(ValueError, match=r"invalid for Python 3.11: backend/mod.py"):
            self.publication(source).validate_for_host(source, self.HOST, {self.TARGET})

    @pytest.mark.parametrize("changes", [{"format": True}, {"extra": 1}, {"source_revision": "../x"}])
    def test_publication_metadata_is_strict(self, changes: dict[str, Any]) -> None:
        with pytest.raises(ValueError):
            self.publication(self.source(), **changes)

    def test_files_need_the_frontend_archive_prefix(self) -> None:
        source = self.source()
        metadata = self.publication(source).manifest.model_dump_json()
        with pytest.raises(ValueError, match="must be under files/"):
            OpenWebuiModPublication.from_zip(self.archive({"publication.json": metadata, "secret.py": ""}))

    def test_backend_only_publications_have_no_browser_files(self) -> None:
        source = OpenWebuiModPackage.from_zip(self.archive({
            "mod.json": json.dumps({"format": 1, "id": "backend", "name": "Backend", "version": "1",
                                    "backend": "mod.py"}),
            "mod.py": "raise RuntimeError()",
        }))
        publication = self.publication(source, replacements={})
        with pytest.raises(ValueError, match="backend-only"):
            publication.validate_for_host(source, self.HOST, set())
        publication.files.clear()
        publication.validate_for_host(source, self.HOST, set())

    def test_bootstrap_only_publication_binds_entry_and_assets_to_source(self) -> None:
        source = OpenWebuiModPackage.from_zip(self.archive({
            "mod.json": json.dumps({"format": 1, "id": "startup", "name": "Startup", "version": "1",
                                    "bootstrap": "start.ts"}),
            "start.ts": "export function activate() {}",
            "locales.json": '["en-US"]',
        }))
        publication = self.publication(source, replacements={}, bootstrap="bootstrap/start.ts.mjs")
        publication.files = {"bootstrap/start.ts.mjs": b"export function activate() {}",
                             "bootstrap/locales.json": b'["en-US"]'}
        publication.validate_for_host(source, self.HOST, set())
        publication.manifest.bootstrap = "bootstrap/other.ts.mjs"
        with pytest.raises(ValueError, match="entry points"):
            publication.validate_for_host(source, self.HOST, set())
        publication.manifest.bootstrap = "bootstrap/start.ts.mjs"
        del publication.files["bootstrap/start.ts.mjs"]
        with pytest.raises(ValueError, match="entry file is missing"):
            publication.validate_for_host(source, self.HOST, set())

    @pytest.mark.parametrize("path, content", [
        ("bootstrap/backend/mod.py", b"raise RuntimeError()"),
        ("bootstrap/mod.json", b"{}"),
        ("bootstrap/icon.png", b"changed"),
        ("bootstrap/unknown.png", b"\x89PNG"),
    ])
    def test_bootstrap_asset_prefix_cannot_expose_backend_or_unbound_assets(self, path: str, content: bytes) -> None:
        source = self.source()
        publication = self.publication(source)
        publication.files[path if path.startswith("bootstrap/") else f"frontend/{path}"] = content
        with pytest.raises(ValueError, match="asset must match"):
            publication.validate_for_host(source, self.HOST, {self.TARGET})
