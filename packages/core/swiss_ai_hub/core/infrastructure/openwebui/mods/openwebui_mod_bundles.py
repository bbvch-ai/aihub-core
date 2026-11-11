import hashlib
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import ClassVar
from zipfile import ZipFile, ZipInfo

from mypy_boto3_s3 import S3Client
from starlette.concurrency import run_in_threadpool

from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_store import OpenWebuiModStore
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_package import OpenWebuiModPackage
from swiss_ai_hub.core.persistence.openwebui.openwebui_mod_revision_entity import OpenWebuiModRevisionEntity


class OpenWebuiModBundles:
    """Offer supplied source packages through the same catalog as SysAdmin uploads."""

    NAMES: ClassVar[tuple[str, ...]] = ()
    DEFAULT_ENABLED: ClassVar[frozenset[str]] = frozenset()

    @classmethod
    def packages(cls) -> dict[str, OpenWebuiModPackage]:
        packages = [OpenWebuiModPackage.from_zip(cls.source(name)) for name in cls.NAMES]
        return {package.manifest.id: package for package in packages}

    @classmethod
    async def seed_catalog(cls, client: S3Client) -> None:
        store = OpenWebuiModStore(client)
        for name in cls.NAMES:
            content = await run_in_threadpool(cls.source, name)
            revision = hashlib.sha256(content).hexdigest()
            if await run_in_threadpool(OpenWebuiModRevisionEntity.find_revision, revision) is None:
                await store.upload(content, "aihub-bundled")

    @classmethod
    @lru_cache(maxsize=8)
    def source(cls, name: str) -> bytes:
        if name not in cls.NAMES:
            raise ValueError(f"Unknown bundled mod: {name}")
        directory = Path(__file__).parent / "bundled" / name
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
