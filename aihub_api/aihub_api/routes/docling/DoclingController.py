import logging
from typing import Annotated, Self

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.routes.Controller import Controller
from fastapi import HTTPException, Request, Security

from aihub_api.i18n.ApiLocaleString import ApiLocaleString
from aihub_api.routes.docling.DoclingMappings import FormatToExtensions, MimeTypeToFormat
from aihub_api.routes.docling.DoclingService import DoclingService
from aihub_api.routes.docling.dto.DocumentConversionResponse import DocumentConversionResponse

logger = logging.getLogger(__name__)


class DoclingController(Controller):
    name = ApiLocaleString.from_i18n_path("api.controllers.docling.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.docling.description")
    icon = "mage:file"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/docling", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def parse_document(self, route: str = "/process") -> Self:
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
