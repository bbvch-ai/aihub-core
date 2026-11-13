import hashlib
import logging
from typing import ClassVar, Literal

from botocore.exceptions import ClientError
from mypy_boto3_s3 import S3Client
from starlette.concurrency import run_in_threadpool

from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_host import OpenWebuiModHost
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_package import OpenWebuiModPackage
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_publication import OpenWebuiModPublication
from swiss_ai_hub.core.infrastructure.s3.s3_bucket_provisioner import S3BucketProvisioner
from swiss_ai_hub.core.persistence.openwebui.openwebui_mod_entity import OpenWebuiModEntity


class OpenWebuiModStore:
    BUCKET: ClassVar[str] = "openwebui-mods"

    def __init__(self, client: S3Client) -> None:
        self.client = client

    async def install(
        self, source: bytes, compiled: bytes, installed_by: str, host: OpenWebuiModHost,
    ) -> OpenWebuiModEntity:
        package = await run_in_threadpool(OpenWebuiModPackage.from_zip, source)
        publication = await run_in_threadpool(OpenWebuiModPublication.from_zip, compiled)
        await run_in_threadpool(publication.validate_for_host, package, host.compatibility, host.components, host.callables)
        await run_in_threadpool(self._write_archive, package.revision, source, "sources")
        await run_in_threadpool(self._write_archive, publication.revision, compiled, "publications")
        return await run_in_threadpool(OpenWebuiModEntity.install, package, publication, installed_by, len(compiled))

    async def read_archive(self, revision: str) -> bytes:
        return await run_in_threadpool(self._read_archive, revision, "sources")

    async def read_publication(self, revision: str) -> bytes:
        return await run_in_threadpool(self._read_archive, revision, "publications")

    async def prune(self) -> None:
        try:
            await run_in_threadpool(self._prune)
        except Exception:
            # The installed record is authoritative; failed cleanup must not turn a successful install into an error.
            logging.getLogger(__name__).exception("Could not clean obsolete mod archives; retrying on the next installation")

    def _prune(self) -> None:
        keep = {key for mod in OpenWebuiModEntity.installed() for key in (
            f"sources/{mod.source_revision}.zip", f"publications/{mod.publication}.zip",
        )}
        for page in self.client.get_paginator("list_objects_v2").paginate(Bucket=self.BUCKET):
            obsolete = [{"Key": obj["Key"]} for obj in page.get("Contents", [])
                        if obj["Key"].startswith(("sources/", "publications/")) and obj["Key"] not in keep]
            if obsolete:
                result = self.client.delete_objects(Bucket=self.BUCKET, Delete={"Objects": obsolete, "Quiet": True})
                if result.get("Errors"):
                    raise RuntimeError("Object storage could not delete obsolete mod archives")

    def _write_archive(self, revision: str, content: bytes, prefix: Literal["sources", "publications"]) -> None:
        if not S3BucketProvisioner.bucket_exists(self.client, self.BUCKET):
            try:
                self.client.create_bucket(Bucket=self.BUCKET)
            except ClientError as error:
                if error.response["Error"]["Code"] != "BucketAlreadyOwnedByYou":
                    raise
        self.client.put_object(
            Bucket=self.BUCKET, Key=f"{prefix}/{revision}.zip", Body=content, ContentType="application/zip",
        )

    def _read_archive(self, revision: str, prefix: Literal["sources", "publications"]) -> bytes:
        response = self.client.get_object(Bucket=self.BUCKET, Key=f"{prefix}/{revision}.zip")
        body = response["Body"]
        try:
            content = body.read(OpenWebuiModPackage.MAX_ARCHIVE_BYTES + 1)
        finally:
            body.close()
        if len(content) > OpenWebuiModPackage.MAX_ARCHIVE_BYTES or hashlib.sha256(content).hexdigest() != revision:
            raise RuntimeError(f"Stored Open WebUI mod archive failed its integrity check: {revision}")
        return content
