import base64
import logging
import time
from datetime import datetime
from typing import Annotated, Any

import httpx
import jwt
from swiss_ai_hub.core.incident import IncidentSettings

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
API_VERSION = "2022-11-28"
REQUEST_TIMEOUT_SECONDS = 30

# GitHub rejects an App JWT older than 10 minutes and back-dating absorbs clock skew
# between this container and GitHub, which is the usual cause of a puzzling 401.
JWT_LIFETIME_SECONDS = 540
JWT_BACKDATE_SECONDS = 60

# An installation token lasts an hour; retiring it early keeps a long request from
# starting with a token that expires mid-flight.
TOKEN_REFRESH_MARGIN_SECONDS = 300


class GitHubIssueClient:
    """Files an incident as an issue, with its attachments committed alongside.

    Attachments go into the repository rather than being attached to the issue the way a
    person can in the browser: that upload endpoint is undocumented and rejects App
    installation tokens outright, so a server cannot use it. Committed files referenced from
    the body render inline in the issue, which is the same result by a supported route.
    """

    def __init__(self, settings: Annotated[IncidentSettings, "Deployment's incident configuration"]):
        self._settings = settings
        self._token: str | None = None
        self._token_expires_at: float = 0.0
        self._repository_is_private: bool | None = None

    @property
    def _repository(self) -> str:
        return self._settings.GITHUB_REPOSITORY or ""

    def _app_jwt(self) -> str:
        now = int(time.time())
        return jwt.encode(
            {"iat": now - JWT_BACKDATE_SECONDS, "exp": now + JWT_LIFETIME_SECONDS, "iss": self._settings.GITHUB_APP_ID},
            self._settings.GITHUB_PRIVATE_KEY,
            algorithm="RS256",
        )

    async def _installation_token(self, client: httpx.AsyncClient) -> str:
        if self._token and time.time() < self._token_expires_at - TOKEN_REFRESH_MARGIN_SECONDS:
            return self._token

        response = await client.post(
            f"{GITHUB_API}/app/installations/{self._settings.GITHUB_INSTALLATION_ID}/access_tokens",
            headers=self._headers(self._app_jwt()),
        )
        response.raise_for_status()
        payload = response.json()
        self._token = payload["token"]
        self._token_expires_at = datetime.fromisoformat(payload["expires_at"]).timestamp()
        return self._token

    @staticmethod
    def _headers(token: str) -> dict[str, str]:
        return {
            "authorization": f"Bearer {token}",
            "accept": "application/vnd.github+json",
            "x-github-api-version": API_VERSION,
        }

    async def ensure_repository_is_private(self) -> None:
        """Refuse to file anything into a public repository.

        A report carries a customer's prompts and screenshots. Publishing those cannot be undone,
        so a misconfigured repository name has to stop the feature rather than be discovered later
        by whoever finds the issues on the open internet. Checked once and remembered.
        """
        if self._repository_is_private:
            return

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            token = await self._installation_token(client)
            response = await client.get(f"{GITHUB_API}/repos/{self._repository}", headers=self._headers(token))
            response.raise_for_status()
            repository = response.json()

        if not repository.get("private"):
            raise PermissionError(
                f"Incident repository {self._repository} is public. Reports carry customer data and will not be filed."
            )
        self._repository_is_private = True

    async def create_issue(
        self,
        title: Annotated[str, "Issue title"],
        body: Annotated[str, "Issue body, already rendered as markdown"],
        labels: Annotated[list[str], "Labels the form declares"],
    ) -> Annotated[dict[str, Any], "Created issue as GitHub returned it"]:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            token = await self._installation_token(client)
            response = await client.post(
                f"{GITHUB_API}/repos/{self._repository}/issues",
                headers=self._headers(token),
                json={"title": title, "body": body, "labels": labels},
            )
            response.raise_for_status()
            return response.json()

    async def commit_attachment(
        self,
        path: Annotated[str, "Path inside the repository"],
        content: Annotated[bytes, "File bytes"],
        message: Annotated[str, "Commit message"],
    ) -> Annotated[str, "Permanent URL of the committed file"]:
        """Commits one file and returns a URL that still resolves next month.

        Returns `html_url` — the file's page in the repository — and deliberately not
        `download_url`: on a private repository that one carries a short-lived `?token=`, so an
        issue body built from it shows working attachments the day it is filed and broken ones
        afterwards, which is worse than a link.

        Uses the contents API, which takes base64 in a single call. It is documented for files up
        to 100 MB, well past the cap a report is allowed anyway, so the blob-and-tree dance buys
        nothing here.
        """
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            token = await self._installation_token(client)
            response = await client.put(
                f"{GITHUB_API}/repos/{self._repository}/contents/{path}",
                headers=self._headers(token),
                json={"message": message, "content": base64.b64encode(content).decode()},
            )
            response.raise_for_status()
            return response.json()["content"]["html_url"]
