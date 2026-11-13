from functools import lru_cache
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, ZipInfo

from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_package import OpenWebuiModPackage


class OpenWebuiModBundles:
    """Offer supplied source packages through the same catalog as SysAdmin uploads."""

    @staticmethod
    def directory() -> Path:
        return Path(__file__).parent / "bundled"

    @classmethod
    def names(cls) -> tuple[str, ...]:
        return tuple(sorted(path.parent.name for path in cls.directory().glob("*/mod.json") if path.is_file()))

    @classmethod
    def packages(cls) -> dict[str, OpenWebuiModPackage]:
        packages: dict[str, OpenWebuiModPackage] = {}
        for name in cls.names():
            package = OpenWebuiModPackage.from_zip(cls.source(name))
            if package.manifest.id in packages:
                raise ValueError(f"Duplicate bundled mod ID: {package.manifest.id}")
            packages[package.manifest.id] = package
        return packages

    @classmethod
    def source(cls, name: str) -> bytes:
        if name not in cls.names():
            raise ValueError(f"Unknown bundled mod: {name}")
        return cls._source(cls.directory() / name)

    @classmethod
    @lru_cache(maxsize=8)
    def _source(cls, directory: Path) -> bytes:
        return cls.zip({
            path.relative_to(directory).as_posix(): path.read_bytes()
            for path in directory.rglob("*") if path.is_file()
        })

    @staticmethod
    def zip(files: dict[str, bytes]) -> bytes:
        buffer = BytesIO()
        with ZipFile(buffer, "w") as archive:
            for path, content in sorted(files.items()):
                archive.writestr(ZipInfo(path), content)
        return buffer.getvalue()
