from typing import Annotated

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.generative_ai.document.accessor.S3AnonymousFileAccessService import S3AnonymousFileAccessService
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.s3.use_s3 import use_s3_service
from aihub_lib.routes.Controller import Controller
from fastapi import Body, Depends, Header, Query, Security

from aihub_api.routes.parsing.dto.DocumentConversionResponse import DocumentConversionResponse
from aihub_api.routes.parsing.dto.ImageMode import ImageMode
from aihub_api.routes.parsing.ParsingService import ParsingService


class ParsingController(Controller):
    """
    Controller for document parsing endpoints.

    Implements the OpenWebUI External Document Loader specification:
    - PUT /process: Convert document to markdown
    """

    name = LocaleString(
        en="Document Parser",
        de="Dokumenten-Parser",
        fr="Analyseur de documents",
        it="Analizzatore di documenti",
    )
    description = LocaleString(
        en="Parse and convert documents to markdown format",
        de="Dokumente in Markdown-Format parsen und konvertieren",
        fr="Analyser et convertir des documents au format Markdown",
        it="Analizzare e convertire documenti in formato Markdown",
    )
    icon = "line-md:document"

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
            response_model=DocumentConversionResponse,
        )
        async def process_document(
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            body: Annotated[bytes, Body()],
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
