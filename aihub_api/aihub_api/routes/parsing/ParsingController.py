"""
Document parsing controller.

Exposes REST endpoints for document conversion following the OpenWebUI
External Document Loader specification.
"""

import logging
import urllib.parse
from enum import StrEnum
from typing import Annotated

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller
from fastapi import HTTPException, Query, Request, Security

from aihub_api.routes.parsing.dto.DocumentConversionResponse import DocumentConversionResponse
from aihub_api.routes.parsing.ParsingMappings import FormatToExtensions, MimeTypeToFormat
from aihub_api.routes.parsing.ParsingService import ParsingService


class ImageMode(StrEnum):
    """Image handling mode for parsed documents."""

    S3 = "s3"  # Upload to S3, return signed URLs (default)
    BASE64 = "base64"  # Embed images as base64 data URIs in markdown

logger = logging.getLogger(__name__)


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
        """
        Register the document parsing endpoint.

        PUT /process - Convert document to markdown

        Following OpenWebUI External Document Loader specification:
        - Request body: Raw binary file content
        - Headers:
          - Content-Type: MIME type of the file
          - X-Filename: URL-encoded original filename
          - Authorization: Bearer token
          - X-OpenWebUI-User-Id (optional): User ID
          - X-OpenWebUI-User-Email (optional): User email
          - X-OpenWebUI-User-Name (optional): User name
          - X-OpenWebUI-User-Role (optional): User role
        - Response: DocumentConversionResponse
        """

        @self.router.put(
            route,
            tags=self.tags,
            summary="Process document (OpenWebUI)",
            description="Convert a document to markdown format. Supports PDF, images, and Office documents.",
            response_model=DocumentConversionResponse,
        )
        async def process_document(
            request: Request,
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            image_mode: Annotated[
                ImageMode,
                Query(description="How to handle images: 's3' uploads to S3 and returns signed URLs, 'base64' embeds images as data URIs"),
            ] = ImageMode.S3,
        ) -> DocumentConversionResponse:
            content_type = request.headers.get("content-type", "")
            body = await request.body()

            logger.info(f"Processing document: {len(body)} bytes, content-type: {content_type}")

            # Extract filename from headers (URL-encoded)
            filename = request.headers.get("x-filename") or request.headers.get("x-file-name") or "document"

            # URL decode the filename
            try:
                filename = urllib.parse.unquote(filename)
            except Exception:
                pass

            # Add extension if missing based on content type
            if "." not in filename:
                formats = MimeTypeToFormat.get(content_type, [])
                if formats:
                    extensions = FormatToExtensions.get(formats[0], [])
                    extension = f".{extensions[0]}" if extensions else ".pdf"
                else:
                    extension = ".pdf"
                filename += extension

            # Log OpenWebUI user context if provided
            user_id = request.headers.get("x-openwebui-user-id")
            user_email = request.headers.get("x-openwebui-user-email")
            if user_id or user_email:
                logger.debug(f"OpenWebUI user context: id={user_id}, email={user_email}")

            try:
                return await ParsingService.convert_from_bytes(
                    content=body,
                    filename=filename,
                    content_type=content_type,
                    image_mode=image_mode,
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error processing document: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Error processing document")

        return self
