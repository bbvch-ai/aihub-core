import hashlib
from typing import ClassVar, Literal

from botocore.exceptions import ClientError
from mypy_boto3_s3 import S3Client
from starlette.concurrency import run_in_threadpool

from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_host import OpenWebuiModHost
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_package import OpenWebuiModPackage
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_publication import OpenWebuiModPublication
from swiss_ai_hub.core.infrastructure.s3.s3_bucket_provisioner import S3BucketProvisioner
from swiss_ai_hub.core.persistence.openwebui.openwebui_mod_revision_entity import OpenWebuiModRevisionEntity
from swiss_ai_hub.core.persistence.openwebui.openwebui_mod_publication_entity import OpenWebuiModPublicationEntity


class OpenWebuiModStore:
    BUCKET: ClassVar[str] = "openwebui-mods"

    def __init__(self, client: S3Client):
        self.client = client

    async def upload(self, content: bytes, uploaded_by: str) -> OpenWebuiModRevisionEntity:
        package = await run_in_threadpool(OpenWebuiModPackage.from_zip, content)
        await run_in_threadpool(self._write_archive, package.revision, content)
        # A failed metadata write leaves an unreferenced object; retrying the same upload repairs it.
        return await run_in_threadpool(OpenWebuiModRevisionEntity.record_upload, package, len(content), uploaded_by)

    async def read_archive(self, revision: str) -> bytes:
        return await run_in_threadpool(self._read_archive, revision)

    async def publish(
        self, content: bytes, source_revision: str, published_by: str, host: OpenWebuiModHost
    ) -> OpenWebuiModPublicationEntity:
        source = await run_in_threadpool(OpenWebuiModPackage.from_zip, await self.read_archive(source_revision))
        publication = await run_in_threadpool(OpenWebuiModPublication.from_zip, content)
        await run_in_threadpool(publication.validate_for_host, source, host.compatibility, host.components, host.callables)
        await run_in_threadpool(self._write_archive, publication.revision, content, "publications")
        return await run_in_threadpool(
            OpenWebuiModPublicationEntity.record_publication, publication, source.manifest.id, len(content), published_by
        )

    async def read_publication(self, revision: str) -> bytes:
        return await run_in_threadpool(self._read_archive, revision, "publications")

    def _write_archive(
        self, revision: str, content: bytes, prefix: Literal["sources", "publications"] = "sources"
    ) -> None:
        if not S3BucketProvisioner.bucket_exists(self.client, self.BUCKET):
            try:
                self.client.create_bucket(Bucket=self.BUCKET)
            except ClientError as error:
                if error.response["Error"]["Code"] != "BucketAlreadyOwnedByYou":
                    raise
        self.client.put_object(
            Bucket=self.BUCKET,
            Key=f"{prefix}/{revision}.zip",
            Body=content,
            ContentType="application/zip",
        )

    def _read_archive(self, revision: str, prefix: Literal["sources", "publications"] = "sources") -> bytes:
        response = self.client.get_object(Bucket=self.BUCKET, Key=f"{prefix}/{revision}.zip")
        body = response["Body"]
        try:
            content = body.read(OpenWebuiModPackage.MAX_ARCHIVE_BYTES + 1)
        finally:
            body.close()
        if len(content) > OpenWebuiModPackage.MAX_ARCHIVE_BYTES or hashlib.sha256(content).hexdigest() != revision:
            raise RuntimeError(f"Stored Open WebUI mod archive failed its integrity check: {revision}")
        return content
