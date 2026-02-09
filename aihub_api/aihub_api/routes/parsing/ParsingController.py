from typing import Annotated

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.generative_ai.document.accessor.S3AnonymousFileAccessService import S3AnonymousFileAccessService
from aihub_lib.infrastructure.s3.use_s3 import use_s3_service
from aihub_lib.routes.Controller import Controller
from fastapi import Depends, Header, Query, Security

from aihub_api.i18n.ApiLocaleString import ApiLocaleString
from aihub_api.routes.parsing.dependencies.use_limited_body import use_limited_body
from aihub_api.routes.parsing.dto.DocumentConversionResponse import DocumentConversionResponse
from aihub_api.routes.parsing.dto.ImageMode import ImageMode
from aihub_api.routes.parsing.ParsingService import ParsingService


class ParsingController(Controller):
    """
    Controller for document parsing endpoints.

    Implements the OpenWebUI External Document Loader specification:
    - PUT /process: Convert document to markdown
    """

    name = ApiLocaleString.from_i18n_path("api.controllers.parsing.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.parsing.description")
    icon = "mage:file"

    MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB

    def __init__(
        self,
        *,
        auth: AuthHandler,
        route: str = "/parsing",
        additionally_required_permission: str | None = None,
    ):
        super().__init__(
            auth=auth,
            route=route,
            additionally_required_permission=additionally_required_permission,
        )

    def parse_document(self, route: str = "/process") -> "ParsingController":
        """Register the document parsing endpoint (OpenWebUI External Document Loader spec)."""

        @self.router.put(
            route,
            tags=self.tags,
            summary="Process document (OpenWebUI)",
            description="Convert a document to markdown format. Supports PDF, images, and Office documents.",
        )
        async def process_document(
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            body: Annotated[bytes, Depends(use_limited_body(max_bytes=ParsingController.MAX_FILE_SIZE_BYTES))],
            s3_service: Annotated[S3AnonymousFileAccessService, Depends(use_s3_service)],
            content_type: Annotated[str, Header(include_in_schema=False)] = "",
            x_filename: Annotated[str, Header()] = "document",
            x_file_name: Annotated[str | None, Header()] = None,
            image_mode: Annotated[
                ImageMode,
                Query(description="Image handling: 's3' (signed URLs) or 'base64' (embedded data URIs)"),
            ] = ImageMode.S3,
        ) -> DocumentConversionResponse:
            return await ParsingService.convert_from_bytes(
                content=body,
                filename=x_file_name or x_filename,
                content_type=content_type,
                image_mode=image_mode,
                s3_service=s3_service,
            )

        return self
