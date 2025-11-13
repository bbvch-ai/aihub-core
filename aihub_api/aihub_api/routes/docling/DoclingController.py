import logging
from typing import Annotated

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller
from fastapi import Request, Security

from aihub_api.routes.docling.DoclingService import DoclingService

logger = logging.getLogger(__name__)


class DoclingController(Controller):
    """
    Controller for document conversion using Docling.

    This endpoint acts as a proxy for OpenWebUI when configured with
    CONTENT_EXTRACTION_ENGINE: external and DOCLING_SERVER_URL pointing
    to this API service.

    The controller forwards requests to the internal Docling service
    and returns the conversion results.
    """

    name = LocaleString(en="Document Conversion")
    description = LocaleString(en="Convert documents using Docling service")
    icon = "line-md:document"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/docling", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def process_endpoint(self, route: str = "/process") -> "DoclingController":
        """Process endpoint that OpenWebUI calls for document extraction."""

        @self.router.put(route, tags=self.tags, summary="Process document (OpenWebUI)")
        async def process_document(
            request: Request,
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ):
            """
            Process document for OpenWebUI.

            OpenWebUI sends raw file bytes with Content-Type header indicating file type.
            """
            content_type = request.headers.get("content-type", "")
            body = await request.body()

            logger.info(f"Processing document: {len(body)} bytes, content-type: {content_type}")

            # Extract filename from headers or infer from content-type
            filename = request.headers.get("x-filename") or request.headers.get("x-file-name") or "document"

            if "." not in filename:
                extension_map = {
                    "application/pdf": ".pdf",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
                    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
                    "text/html": ".html",
                    "text/plain": ".txt",
                    "image/png": ".png",
                    "image/jpeg": ".jpg",
                }
                filename += extension_map.get(content_type, ".pdf")

            try:
                return await DoclingService.convert_from_bytes(content=body, filename=filename)
            except Exception as e:
                logger.error(f"Error processing document: {e}", exc_info=True)
                return {"error": str(e)}

        return self
