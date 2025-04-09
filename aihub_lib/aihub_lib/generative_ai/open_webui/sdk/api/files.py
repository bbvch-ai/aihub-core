import os
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union

import httpx

from ..client import BaseClient
from ..models.files import ContentForm, FileModel, FileModelResponse, ProcessFileForm


class FilesClient(BaseClient):
    """
    Client for interacting with the OpenWebUI files API endpoints.

    Provides methods for uploading, listing, downloading, and managing files.

    Example:
        ```python
        from sdk import OpenWebuiClient
        import asyncio

        async def upload_example():
            client = OpenWebuiClient(token="your-token")

            # Upload a file
            with open("document.pdf", "rb") as f:
                file = await client.files.upload_file(f, "document.pdf")

            # List all user files
            files = await client.files.list_files()

            # Download a file
            content = await client.files.get_file_content(file.id)
            with open("downloaded.pdf", "wb") as f:
                f.write(content)

        asyncio.run(upload_example())
        ```
    """

    async def upload_file(
        self,
        file: Union[BinaryIO, bytes, str, Path],
        filename: Optional[str] = None,
        process: bool = True,
    ) -> FileModelResponse:
        """Upload a file to OpenWebUI storage"""
        url = self._get_url("/api/v1/files/")
        headers = self._get_headers()
        # Remove Content-Type from headers as it will be set by the form
        if "Content-Type" in headers:
            del headers["Content-Type"]

        params = {"process": "true" if process else "false"}

        # Handle different file input types
        if isinstance(file, (str, Path)):
            path = Path(file)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            filename = filename or path.name
            with open(path, "rb") as f:
                file_content = f.read()
        elif isinstance(file, bytes):
            file_content = file
            filename = filename or "file"
        else:
            # Assume it's a file-like object
            file_content = file.read()
            if hasattr(file, "name") and not filename:
                filename = os.path.basename(file.name)
            filename = filename or "file"

            # Reset file position if possible
            if hasattr(file, "seek"):
                file.seek(0)

        files = {"file": (filename, file_content)}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, params=params, files=files)
            response.raise_for_status()
            return FileModelResponse.model_validate(response.json())

    async def list_files(self, include_content: bool = True) -> List[FileModelResponse]:
        """List all files accessible to the authenticated user"""
        params = {"content": "true" if include_content else "false"}
        response = await self.get("/api/v1/files/", params=params)
        return [FileModelResponse.model_validate(file) for file in response.json()]

    async def delete_all_files(self) -> Dict[str, Any]:
        """Delete all files (admin only)"""
        response = await self.delete("/api/v1/files/all")
        return response.json()

    async def get_file(self, file_id: str) -> FileModel:
        """Get file metadata and information by ID"""
        response = await self.get(f"/api/v1/files/{file_id}")
        return FileModel.model_validate(response.json())

    async def get_file_data_content(self, file_id: str) -> str:
        """Get the text content of a file by ID"""
        response = await self.get(f"/api/v1/files/{file_id}/data/content")
        return response.json().get("content", "")

    async def update_file_content(self, file_id: str, content: str) -> Dict[str, Any]:
        """Update the text content of a file by ID"""
        form_data = ContentForm(content=content)
        response = await self.post(f"/api/v1/files/{file_id}/data/content/update", json_data=form_data.model_dump())
        return response.json()

    async def get_file_content(
        self, file_id: str, output_path: Optional[Union[str, Path]] = None, as_attachment: bool = False
    ) -> Optional[bytes]:
        """
        Get the raw content of a file by ID

        Returns bytes if output_path is None, otherwise saves to file and returns None
        """
        params = {"attachment": "true" if as_attachment else "false"}
        url = self._get_url(f"/api/v1/files/{file_id}/content")
        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()

            if output_path:
                path = Path(output_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(response.content)
                return None
            else:
                return response.content

    async def get_html_content(self, file_id: str) -> bytes:
        """Get HTML content of a file by ID"""
        url = self._get_url(f"/api/v1/files/{file_id}/content/html")
        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.content

    async def process_file(self, file_id: str, content: Optional[str] = None) -> Dict[str, Any]:
        """Process a file with optional content override"""
        form_data = ProcessFileForm(file_id=file_id, content=content)
        # This endpoint is not directly exposed in the router, but is used internally
        response = await self.post("/api/v1/retrieval/process", json_data=form_data.model_dump())
        return response.json()

    async def delete_file(self, file_id: str) -> Dict[str, Any]:
        """Delete a file by ID"""
        response = await self.delete(f"/api/v1/files/{file_id}")
        return response.json()
