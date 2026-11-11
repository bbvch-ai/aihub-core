import hashlib
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, ZipInfo

from mypy_boto3_s3 import S3Client
from starlette.concurrency import run_in_threadpool

from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_store import OpenWebuiModStore
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_package import OpenWebuiModPackage
from swiss_ai_hub.core.persistence.openwebui.openwebui_mod_revision_entity import OpenWebuiModRevisionEntity


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
    async def seed_catalog(cls, client: S3Client) -> None:
        store = OpenWebuiModStore(client)
        for name in cls.names():
            content = await run_in_threadpool(cls.source, name)
            revision = hashlib.sha256(content).hexdigest()
            if await run_in_threadpool(OpenWebuiModRevisionEntity.find_revision, revision) is None:
                await store.upload(content, "aihub-bundled")

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
