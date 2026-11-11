import hashlib
import json
import stat
from io import BytesIO
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import pytest

from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_package import OpenWebuiModPackage

pytestmark = pytest.mark.unit


class TestOpenWebuiModPackage:
    @staticmethod
    def manifest(**changes: Any) -> dict[str, Any]:
        return {
            "format": 1,
            "id": "chat-tools",
            "name": "Chat tools",
            "version": "1.0.0",
            "replacements": {"src/lib/components/layout/Sidebar/UserMenu.svelte": "frontend/Menu.svelte"},
            "backend": "backend/mod.py",
            **changes,
        }

    @staticmethod
    def archive(files: list[tuple[str | ZipInfo, bytes]]) -> bytes:
        output = BytesIO()
        with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
            for path, content in files:
                archive.writestr(path, content)
        return output.getvalue()

    @classmethod
    def package(cls, **changes: Any) -> bytes:
        return cls.archive(
            [
                ("mod.json", json.dumps(cls.manifest(**changes)).encode()),
                ("frontend/Menu.svelte", b'<script>import {label} from "./label.js";</script><button>{label}</button>'),
                ("frontend/label.js", b'export const label = "Chat settings";'),
                ("frontend/icon.png", b"\x89PNG\r\n\x1a\n"),
                ("backend/mod.py", b'raise RuntimeError("Uploading must not execute this module")'),
                ("backend/helper.py", b"VALUE = 1\n"),
            ]
        )

    def test_full_stack_package_retains_sources_helpers_and_assets_without_executing_code(self) -> None:
        content = self.package()

        package = OpenWebuiModPackage.from_zip(content)

        assert package.manifest.id == "chat-tools"
        assert package.manifest.backend == "backend/mod.py"
        assert package.files["frontend/icon.png"] == b"\x89PNG\r\n\x1a\n"
        assert "backend/helper.py" in package.files
        assert package.revision == hashlib.sha256(content).hexdigest()

    def test_invalid_settings_control_reports_the_field_during_upload(self) -> None:
        content = self.package(settings_fields={"message": {"control": "primeTextare"}})
        with pytest.raises(ValueError) as caught:
            OpenWebuiModPackage.from_zip(content)
        message = str(caught.value)
        assert "Field 'message': unknown control 'primeTextare'" in message
        assert "tagged-union" not in message

    @pytest.mark.parametrize("changes", [{"backend_restart_required": "false"}, {"backend_restart_required": True, "backend": None}])
    def test_restart_declaration_requires_a_boolean_and_backend_entry(self, changes: dict[str, Any]) -> None:
        with pytest.raises(ValueError):
            OpenWebuiModPackage.from_zip(self.package(**changes))

    @pytest.mark.parametrize(
        "changes",
        [
            {"backend": None},
            {"replacements": {}},
            {"backend": None, "replacements": {}, "frontend": "frontend/label.js"},
        ],
    )
    def test_a_package_can_have_only_one_side(self, changes: dict[str, Any]) -> None:
        assert OpenWebuiModPackage.from_zip(self.package(**changes)).manifest.id == "chat-tools"

    def test_changing_backend_or_frontend_changes_the_package_revision(self) -> None:
        original = OpenWebuiModPackage.from_zip(self.package())
        for path in ["backend/mod.py", "frontend/Menu.svelte"]:
            files = {**original.files, path: original.files[path] + b"\n"}
            changed = OpenWebuiModPackage.from_zip(self.archive(list(files.items())))
            assert changed.revision != original.revision

    @pytest.mark.parametrize("content", [b"", b"not a zip", b"PK\x03\x04"])
    def test_invalid_archive_is_rejected(self, content: bytes) -> None:
        with pytest.raises(ValueError, match="Invalid mod ZIP"):
            OpenWebuiModPackage.from_zip(content)

    @pytest.mark.parametrize(
        "path",
        [
            "../escape.py",
            "/absolute.py",
            "x/../../escape.py",
            "x/./code.py",
            "x//code.py",
            "C:/code.py",
            "x\\code.py",
            "x%2Fcode.py",
            ".",
            "code.py?query",
            "code.py#hash",
        ],
    )
    def test_noncanonical_paths_are_rejected(self, path: str) -> None:
        with pytest.raises(ValueError, match="package path"):
            OpenWebuiModPackage.from_zip(self.archive([(path, b"source")]))

    def test_duplicate_file_is_rejected(self) -> None:
        with pytest.warns(UserWarning, match="Duplicate name"):
            content = self.archive([("mod.json", b"{}"), ("mod.json", b"{}")])
        with pytest.raises(ValueError, match="Duplicate mod archive path"):
            OpenWebuiModPackage.from_zip(content)

    def test_duplicate_manifest_keys_are_rejected(self) -> None:
        with pytest.raises(ValueError, match="Duplicate manifest key: format"):
            OpenWebuiModPackage.from_zip(self.archive([("mod.json", b'{"format":1,"format":1}')]))

    def test_symbolic_links_are_rejected(self) -> None:
        link = ZipInfo("frontend/link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        with pytest.raises(ValueError, match="link or special file"):
            OpenWebuiModPackage.from_zip(self.archive([(link, b"../../outside")]))

    def test_file_cannot_also_be_a_parent_directory(self) -> None:
        with pytest.raises(ValueError, match="file as its parent"):
            OpenWebuiModPackage.from_zip(self.archive([("frontend", b"file"), ("frontend/mod.js", b"source")]))

    def test_normal_directory_entries_are_allowed(self) -> None:
        package = OpenWebuiModPackage.from_zip(self.package())
        content = self.archive([("frontend/", b""), *package.files.items()])
        assert OpenWebuiModPackage.from_zip(content).files == package.files

    def test_manifest_must_be_at_the_archive_root(self) -> None:
        with pytest.raises(ValueError, match="mod.json at its root"):
            OpenWebuiModPackage.from_zip(self.archive([("folder/mod.json", b"{}")]))

    def test_manifest_entry_must_exist(self) -> None:
        with pytest.raises(ValueError, match="missing: backend/missing.py"):
            OpenWebuiModPackage.from_zip(self.package(backend="backend/missing.py"))

    @pytest.mark.parametrize("path", ["backend/my-mod.py", "backend.v1/main.py", "123/main.py"])
    def test_backend_entry_must_support_normal_python_imports(self, path: str) -> None:
        with pytest.raises(ValueError, match="importable Python module path"):
            OpenWebuiModPackage.from_zip(self.package(backend=path))

    @pytest.mark.parametrize(
        "changes",
        [
            {"format": 2},
            {"format": True},
            {"id": "../bad"},
            {"unknown": True},
            {"replacements": {}, "backend": None},
            {"backend": "frontend/label.js"},
            {"frontend": "backend/mod.py"},
            {"replacements": {"not-a-component": "frontend/Menu.svelte"}},
        ],
    )
    def test_invalid_manifest_is_rejected(self, changes: dict[str, Any]) -> None:
        with pytest.raises(ValueError):
            OpenWebuiModPackage.from_zip(self.package(**changes))

    def test_entry_source_must_be_utf8(self) -> None:
        package = OpenWebuiModPackage.from_zip(self.package())
        files = {**package.files, "backend/mod.py": b"\xff"}
        with pytest.raises(ValueError):
            OpenWebuiModPackage.from_zip(self.archive(list(files.items())))

    def test_compressed_payload_cannot_exceed_expanded_limit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(OpenWebuiModPackage, "MAX_EXPANDED_BYTES", 1024)
        with pytest.raises(ValueError, match="Expanded mod archive"):
            OpenWebuiModPackage.from_zip(self.archive([("large.txt", b"x" * 2048)]))

    def test_entry_count_is_bounded(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(OpenWebuiModPackage, "MAX_ENTRIES", 1)
        with pytest.raises(ValueError, match="entry limit"):
            OpenWebuiModPackage.from_zip(self.archive([("one", b""), ("two", b"")]))

    def test_upload_size_is_bounded(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(OpenWebuiModPackage, "MAX_ARCHIVE_BYTES", 1)
        with pytest.raises(ValueError, match="upload limit"):
            OpenWebuiModPackage.from_zip(self.package())
