from typing import Annotated, Literal, Self

from fastapi import Depends, Header, HTTPException, Path, Response, Security
from mypy_boto3_s3 import S3Client
from pydantic import ValidationError
from swiss_ai_hub.core.auth import OpenWebuiAuthHandler, TokenAuthHandler, UserIdentity
from swiss_ai_hub.core.infrastructure import use_s3
from swiss_ai_hub.core.infrastructure.openwebui import OpenWebuiModCompatibility
from swiss_ai_hub.core.routes import Controller

from swiss_ai_hub.api.routes.openai.mods.openwebui_mod_runtime_configuration import OpenWebuiModRuntimeConfiguration
from swiss_ai_hub.api.routes.openai.mods.openwebui_mod_runtime_service import OpenWebuiModRuntimeService


class OpenWebuiModController(Controller):
    def __init__(self, *, additionally_required_permission: str | None = None) -> None:
        super().__init__(
            auth=OpenWebuiAuthHandler(base_auth_handler=TokenAuthHandler()),
            route="/mods",
            additionally_required_permission=additionally_required_permission,
        )

    @property
    def service_name(self) -> str:
        return "openai"

    @staticmethod
    def _compatibility_header(
        compatibility: Annotated[str, Header(alias="X-AIHub-Mod-Compatibility")],
    ) -> OpenWebuiModCompatibility:
        try:
            return OpenWebuiModCompatibility.model_validate_json(compatibility)
        except ValidationError as error:
            raise HTTPException(status_code=422, detail="Invalid Open WebUI host compatibility header.") from error

    def resolve_mod_configuration(self, route: str = "/configuration") -> Self:
        @self.router.post(route)
        async def resolve_openwebui_mod_configuration(
            compatibility: OpenWebuiModCompatibility,
            response: Response,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> OpenWebuiModRuntimeConfiguration:
            """Resolves current tenant selections using Open WebUI's service token and signed user headers."""
            response.headers["Cache-Control"] = "no-store"
            return await OpenWebuiModRuntimeService.resolve_configuration(user, compatibility)

        return self

    def download_mod_archive(self, route: str = "/publications/{revision}/{kind}") -> Self:
        @self.router.get(
            route,
            response_class=Response,
            responses={200: {"content": {"application/zip": {"schema": {"type": "string", "format": "binary"}}}}},
        )
        async def download_openwebui_mod_archive(
            revision: Annotated[str, Path(pattern=r"^[a-f0-9]{64}$")],
            kind: Literal["frontend", "source"],
            compatibility: Annotated[OpenWebuiModCompatibility, Depends(self._compatibility_header)],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            client: Annotated[S3Client, Depends(use_s3)],
        ) -> Response:
            content = await OpenWebuiModRuntimeService.read_archive(user, compatibility, revision, kind, client)
            return Response(
                content,
                media_type="application/zip",
                headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
            )

        return self

    def check_mod_publication(self, route: str = "/publications/{revision}/frontend") -> Self:
        @self.router.head(route, response_class=Response)
        async def check_openwebui_mod_publication(
            revision: Annotated[str, Path(pattern=r"^[a-f0-9]{64}$")],
            compatibility: Annotated[OpenWebuiModCompatibility, Depends(self._compatibility_header)],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> Response:
            """Reauthorizes a cached archive without downloading it again."""
            publication = await OpenWebuiModRuntimeService.authorize_publication(user, compatibility, revision)
            return Response(
                media_type="application/zip",
                headers={
                    "Content-Length": str(publication.archive_bytes),
                    "Cache-Control": "no-store",
                },
            )

        return self
