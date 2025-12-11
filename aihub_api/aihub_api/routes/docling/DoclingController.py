import logging
from typing import Annotated

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller
from fastapi import HTTPException, Request, Security

from aihub_api.routes.docling.DoclingMappings import FormatToExtensions, MimeTypeToFormat
from aihub_api.routes.docling.DoclingService import DoclingService
from aihub_api.routes.docling.dto.DocumentConversionResponse import DocumentConversionResponse

logger = logging.getLogger(__name__)


class DoclingController(Controller):
    name = LocaleString(
        en="Document Converter",
        de="Dokumentenkonverter",
        fr="Convertisseur de documents",
        it="Convertitore di documenti",
    )
    description = LocaleString(
        en="Convert documents to different formats",
        de="Dokumente in verschiedene Formate konvertieren",
        fr="Convertissez des documents en différents formats",
        it="Converti documenti in formati diversi",
    )
    icon = "line-md:document"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/docling", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def parse_document(self, route: str = "/process") -> "DoclingController":
        @self.router.put(
            route, tags=self.tags, summary="Process document (OpenWebUI)", response_model=DocumentConversionResponse
        )
        async def process_document(
            request: Request,
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> DocumentConversionResponse:
            content_type = request.headers.get("content-type", "")
            body = await request.body()

            logger.info(f"Processing document: {len(body)} bytes, content-type: {content_type}")

            filename = request.headers.get("x-filename") or request.headers.get("x-file-name") or "document"

            if "." not in filename:
                formats = MimeTypeToFormat.get(content_type, [])
                if formats:
                    extensions = FormatToExtensions.get(formats[0], [])
                    extension = f".{extensions[0]}" if extensions else ".pdf"
                else:
                    extension = ".pdf"
                filename += extension

            try:
                return await DoclingService.convert_from_bytes(content=body, filename=filename)
            except Exception as e:
                logger.error(f"Error processing document: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Error processing document")

        return self
