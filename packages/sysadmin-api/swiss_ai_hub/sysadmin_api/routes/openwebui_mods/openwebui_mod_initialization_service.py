from fastapi import HTTPException
from mypy_boto3_s3 import S3Client
from swiss_ai_hub.core.infrastructure.openwebui import (
    OpenWebuiModBundles, OpenWebuiModDefaults, OpenWebuiModResolver,
)

from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.dto.openwebui_mod_revision_response import OpenWebuiModRevisionResponse
from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.openwebui_mod_service import OpenWebuiModService


class OpenWebuiModInitializationService:
    @staticmethod
    async def builtins(client: S3Client) -> list[OpenWebuiModRevisionResponse]:
        await OpenWebuiModBundles.seed_catalog(client)
        return [await OpenWebuiModService.get_revision(package.revision) for package in OpenWebuiModBundles.packages().values()]

    @staticmethod
    async def initialize(revisions: dict[str, str]) -> None:
        expected = {mod_id: package.revision for mod_id, package in OpenWebuiModBundles.packages().items()}
        if revisions != expected:
            raise HTTPException(409, "AI Hub's built-in sources changed during initialization. Retry with the current release.")
        host = await OpenWebuiModService.get_host()
        configuration = OpenWebuiModDefaults.configuration()
        for mod in configuration.mods:
            mod.enabled = True
        try:
            await OpenWebuiModResolver.resolve(configuration, host.compatibility)
        except ValueError as error:
            raise HTTPException(409, str(error)) from error
