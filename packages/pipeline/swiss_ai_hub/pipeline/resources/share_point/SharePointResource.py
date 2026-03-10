import asyncio
import os
import re
from datetime import datetime
from typing import Annotated

import aiohttp
import requests
from dagster import ConfigurableResource
from pydantic import Field, PrivateAttr
from swiss_ai_hub.core.infrastructure.sharepoint.SharePointSettings import SharePointSettings

from swiss_ai_hub.pipeline.types.SharePointFile import MinimalSharePointFile, SharePointFile


def _parse_sharepoint_datetime(dt_str: str) -> int:
    """Convert SharePoint ISO datetime string to Unix timestamp."""
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    return int(dt.timestamp())


class SharePointResource(ConfigurableResource):
    target_folders: Annotated[
        list[str] | None,
        Field(description="List of folder paths to fetch files from. If None, fetches from root."),
    ] = None
    exclude_folders: Annotated[
        list[str] | None,
        Field(
            default_factory=lambda: [r".*archiv.*"],
            description="List of regular expressions. "
            "Any folder whose name matches one of these patterns (case-insensitive) will be excluded.",
        ),
    ]
    supported_filetypes: Annotated[
        list[str] | None,
        Field(
            default=None,
            description="Optional list of regex patterns to filter files by extension. "
            "None (default) = allow ALL file types. "
            "Provide a list to restrict to specific types, e.g., [r'\\.pdf$', r'\\.docx?$']",
        ),
    ]
    max_retries: Annotated[
        int,
        Field(
            default=5,
            ge=1,
            le=10,
            description="Maximum number of retry attempts for failed HTTP requests (1-10).",
        ),
    ]
    initial_retry_delay: Annotated[
        float,
        Field(
            default=1.0,
            ge=0.1,
            le=10.0,
            description="Initial delay in seconds between retry attempts. "
            "Delay doubles after each failed attempt (0.1-10.0).",
        ),
    ]

    _access_token: str | None = PrivateAttr(default=None)
    _token_expiry: datetime | None = PrivateAttr(default=None)
    _site_id: str | None = PrivateAttr(default=None)
    _drive_id: str | None = PrivateAttr(default=None)
    _compiled_exclude_patterns: list[re.Pattern] | None = PrivateAttr(default=None)
    _compiled_include_patterns: list[re.Pattern] | None = PrivateAttr(default=None)
    _settings: SharePointSettings = PrivateAttr(default=None)

    def model_post_init(self, __context) -> None:
        super().model_post_init(__context)

        self._settings = SharePointSettings()

        if self.exclude_folders:
            self._compiled_exclude_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.exclude_folders]
        else:
            self._compiled_exclude_patterns = []

        if self.supported_filetypes is None:
            self._compiled_include_patterns = None
        else:
            self._compiled_include_patterns = [
                re.compile(pattern, re.IGNORECASE) for pattern in self.supported_filetypes
            ]

    def _get_access_token(self) -> str:
        if self._access_token and self._token_expiry and datetime.now() < self._token_expiry:
            return self._access_token

        token_url = f"https://login.microsoftonline.com/{self._settings.TENANT_ID}/oauth2/v2.0/token"
        token_data = {
            "grant_type": "client_credentials",
            "client_id": self._settings.CLIENT_ID,
            "client_secret": self._settings.CLIENT_SECRET.get_secret_value(),
            "scope": "https://graph.microsoft.com/.default",
        }

        response = requests.post(token_url, data=token_data)
        response.raise_for_status()

        token_json = response.json()
        self._access_token = token_json["access_token"]
        self._token_expiry = datetime.fromtimestamp(
            datetime.now().timestamp() + token_json.get("expires_in", 3600) - 300
        )
        return self._access_token

    def _get_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._get_access_token()}", "Content-Type": "application/json"}

    def _get_site_id(self) -> str:
        if self._site_id:
            return self._site_id

        site_url_encoded = self._settings.SITE_URL.replace(":", "%3A")
        graph_url = f"https://graph.microsoft.com/v1.0/sites/{site_url_encoded}"

        response = requests.get(graph_url, headers=self._get_headers())
        response.raise_for_status()

        self._site_id = response.json()["id"]
        return self._site_id

    def _get_drive_id(self) -> str:
        if self._drive_id:
            return self._drive_id

        drives_url = f"https://graph.microsoft.com/v1.0/sites/{self._get_site_id()}/drives"
        response = requests.get(drives_url, headers=self._get_headers())
        response.raise_for_status()

        self._drive_id = response.json()["value"][0]["id"]
        return self._drive_id

    def _get_folder_id_by_path(self, folder_path: str) -> str | None:
        url = f"https://graph.microsoft.com/v1.0/sites/{self._get_site_id()}/drives/{self._get_drive_id()}/root:/{folder_path}"
        response = requests.get(url, headers=self._get_headers())
        return response.json()["id"] if response.status_code == 200 else None

    def _is_file_included(self, filename: str) -> bool:
        if not self._compiled_include_patterns:
            return True

        _, extension = os.path.splitext(filename)
        if not extension:
            return False

        return any(pattern.search(extension.lower()) for pattern in self._compiled_include_patterns)

    @staticmethod
    def _extract_relative_path(parent_path: str, filename: str) -> str:
        if "/root:/" in parent_path:
            return parent_path.split("/root:/", 1)[1] + "/" + filename
        return filename

    def _is_folder_excluded(self, folder_name: str) -> bool:
        if not self._compiled_exclude_patterns:
            return False
        return any(pattern.match(folder_name) for pattern in self._compiled_exclude_patterns)

    def _get_files_from_url(self, url: str) -> list[MinimalSharePointFile]:
        files = []

        while url:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            data = response.json()

            for item in data.get("value", []):
                if "file" in item and self._is_file_included(item["name"]):
                    relative_path = self._extract_relative_path(
                        item.get("parentReference", {}).get("path", ""), item["name"]
                    )
                    files.append(
                        MinimalSharePointFile(
                            name=item["name"],
                            path=relative_path,
                            id=item["id"],
                            size=item.get("size", 0),
                            modified=_parse_sharepoint_datetime(item.get("lastModifiedDateTime", "")),
                            content_type=item.get("file", {}).get("mimeType"),
                            etag=item.get("eTag"),
                            created=_parse_sharepoint_datetime(item.get("createdDateTime", "")),
                        )
                    )
                elif "folder" in item and not self._is_folder_excluded(item["name"]):
                    subfolder_url = (
                        f"https://graph.microsoft.com/v1.0/sites/{self._get_site_id()}/drives/"
                        f"{self._get_drive_id()}/items/{item['id']}/children"
                    )
                    files.extend(self._get_files_from_url(subfolder_url))

            url = data.get("@odata.nextLink")
        return files

    def _get_files_from_folder(self, folder_id: str) -> list[MinimalSharePointFile]:
        url = f"https://graph.microsoft.com/v1.0/sites/{self._get_site_id()}/drives/{self._get_drive_id()}/items/{folder_id}/children"
        return self._get_files_from_url(url)

    def fetch_minimal_files(self, folder_paths: list[str] | None = None) -> list[MinimalSharePointFile]:
        folders_to_scan = folder_paths or self.target_folders or ["root"]
        all_files = []

        for folder_path in folders_to_scan:
            folder_id = "root" if folder_path == "root" else self._get_folder_id_by_path(folder_path)
            if folder_id:
                files = self._get_files_from_folder(folder_id)
                all_files.extend(files)

        return all_files

    def download_file(self, file_id: str) -> SharePointFile:
        site_id = self._get_site_id()
        drive_id = self._get_drive_id()

        metadata_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/items/{file_id}"
        metadata_response = requests.get(metadata_url, headers=self._get_headers())
        metadata_response.raise_for_status()
        file_metadata = metadata_response.json()

        download_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/items/{file_id}/content"
        content_response = requests.get(download_url, headers=self._get_headers())
        content_response.raise_for_status()

        parent_path = file_metadata.get("parentReference", {}).get("path", "")
        relative_path = self._extract_relative_path(parent_path, file_metadata["name"])

        return SharePointFile(
            name=file_metadata["name"],
            path=relative_path,
            content=content_response.content,
            size=file_metadata["size"],
            modified=_parse_sharepoint_datetime(file_metadata["lastModifiedDateTime"]),
            created=_parse_sharepoint_datetime(file_metadata["createdDateTime"]),
            content_type=file_metadata.get("file", {}).get("mimeType"),
            download_url=file_metadata.get("@microsoft.graph.downloadUrl"),
            full_url=file_metadata.get("webUrl", ""),
        )

    async def _make_async_request(self, session: aiohttp.ClientSession, url: str) -> dict:
        headers = self._get_headers()
        delay = self.initial_retry_delay

        for attempt in range(self.max_retries):
            try:
                async with session.get(url, headers=headers) as response:
                    response.raise_for_status()
                    return await response.json()
            except aiohttp.ClientResponseError as e:
                # Only retry on "429 Too Many Requests" errors
                if e.status == 429 and attempt < self.max_retries - 1:
                    retry_after = e.headers.get("Retry-After")
                    wait_time = float(retry_after) if retry_after else delay
                    await asyncio.sleep(wait_time)
                    if not retry_after:
                        delay *= 2
                else:
                    raise
        raise Exception(f"Request failed after {self.max_retries} retries.")

    async def get_minimal_share_point_file_async(
        self, session: aiohttp.ClientSession, file_id: str
    ) -> MinimalSharePointFile:
        site_id = self._get_site_id()
        drive_id = self._get_drive_id()

        metadata_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/items/{file_id}"
        file_metadata = await self._make_async_request(session, metadata_url)

        parent_path = file_metadata.get("parentReference", {}).get("path", "")
        relative_path = self._extract_relative_path(parent_path, file_metadata["name"])

        return MinimalSharePointFile(
            name=file_metadata["name"],
            path=relative_path,
            size=file_metadata["size"],
            modified=_parse_sharepoint_datetime(file_metadata["lastModifiedDateTime"]),
            content_type=file_metadata.get("file", {}).get("mimeType"),
            etag=file_metadata.get("eTag"),
            id=file_metadata["id"],
            created=_parse_sharepoint_datetime(file_metadata["createdDateTime"]),
        )

    async def get_multiple_minimal_share_point_files(self, file_ids: list[str]) -> list[MinimalSharePointFile]:
        timeout = aiohttp.ClientTimeout(total=None, connect=10, sock_read=60)
        connector = aiohttp.TCPConnector(limit=5)

        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            results = []
            batch_size = 50
            for i in range(0, len(file_ids), batch_size):
                batch = file_ids[i : i + batch_size]
                tasks = [self.get_minimal_share_point_file_async(session, file_id) for file_id in batch]
                results.extend(await asyncio.gather(*tasks))
            return results
