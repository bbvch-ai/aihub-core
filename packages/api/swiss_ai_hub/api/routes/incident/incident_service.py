import json
import logging
import re
import secrets
from datetime import UTC, datetime
from typing import Annotated

from fastapi import HTTPException, UploadFile
from pydantic import ValidationError
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.incident import IncidentContext, IncidentSettings, IssueFormParser

from swiss_ai_hub.api.routes.incident.dto.created_incident_dto import CreatedIncidentDTO
from swiss_ai_hub.api.routes.incident.dto.incident_form_dto import IncidentFormDTO
from swiss_ai_hub.api.routes.incident.github_issue_client import GitHubIssueClient
from swiss_ai_hub.api.routes.incident.incident_body_formatter import IncidentBodyFormatter

logger = logging.getLogger(__name__)

# Parsed once, at import: a broken definition then breaks startup and CI rather than
# surfacing to a user who is already annoyed enough to be filing a report.
INCIDENT_FORM = IssueFormParser.load()

UNSAFE_IN_FILENAME = re.compile(r"[^A-Za-z0-9._-]+")
MAX_FILENAME_LENGTH = 80


class IncidentService:
    """Turns a submitted form into an issue in the deployment's incident repository."""

    @staticmethod
    def form(
        context: Annotated[IncidentContext, "What the platform knows about this reporter"],
        settings: Annotated[IncidentSettings, "Deployment's incident configuration"],
    ) -> IncidentFormDTO:
        return IncidentFormDTO.from_form(INCIDENT_FORM, context, settings)

    @classmethod
    async def create(
        cls,
        user: Annotated[UserIdentity, "Authenticated reporter"],
        submission_json: Annotated[str, "Answers, as a JSON object"],
        attachments: Annotated[list[UploadFile], "Files the reporter added"],
        client: Annotated[GitHubIssueClient, "Issue client"],
        settings: Annotated[IncidentSettings, "Deployment's incident configuration"],
    ) -> CreatedIncidentDTO:
        submission = cls._validated(submission_json)
        cls._reject_unacceptable(attachments, settings)
        await client.ensure_repository_is_private()

        reference = cls._reference()
        attachment_urls = await cls._commit_attachments(attachments, reference, client)

        issue = await client.create_issue(
            title=IncidentBodyFormatter.title(INCIDENT_FORM, submission),
            body=IncidentBodyFormatter.body(INCIDENT_FORM, submission, user, attachment_urls),
            labels=INCIDENT_FORM.labels,
        )
        logger.info("Filed incident %s as issue #%s for %s", reference, issue["number"], user.email)
        return CreatedIncidentDTO(number=issue["number"], reference=reference, attachments=len(attachment_urls))

    @staticmethod
    def _validated(submission_json: str) -> dict:
        try:
            answers = json.loads(submission_json)
        except json.JSONDecodeError as malformed:
            raise HTTPException(status_code=422, detail=f"Submission is not valid JSON: {malformed}")
        try:
            # Validating against the form's own schema is what keeps a dropdown answer inside the
            # options the form offers, without a second hand-written copy of those options here.
            return INCIDENT_FORM.submission_model()(**answers).model_dump()
        except ValidationError as invalid:
            raise HTTPException(status_code=422, detail=invalid.errors())

    @staticmethod
    def _reject_unacceptable(attachments: list[UploadFile], settings: IncidentSettings) -> None:
        """Count and size come from the deployment, the accepted extensions from the definition.

        The picker already filters on `accept`, but that is a browser hint and this endpoint is
        reachable without one — so what the definition says is accepted is enforced here too.
        """
        upload = INCIDENT_FORM.upload
        if attachments and not upload:
            raise HTTPException(status_code=400, detail="This form does not accept attachments.")
        if upload and upload.required and not attachments:
            raise HTTPException(status_code=422, detail=f"{upload.label} is required.")
        if len(attachments) > settings.MAX_ATTACHMENTS:
            raise HTTPException(
                status_code=413,
                detail=f"At most {settings.MAX_ATTACHMENTS} files per report, got {len(attachments)}.",
            )
        for attachment in attachments:
            if attachment.size and attachment.size > settings.MAX_ATTACHMENT_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail=f"{attachment.filename} exceeds the {settings.MAX_ATTACHMENT_BYTES} byte limit.",
                )
            if upload and not upload.accepts(attachment.filename or ""):
                raise HTTPException(
                    status_code=415,
                    detail=f"{attachment.filename} is not an accepted file type. Accepted: {', '.join(upload.accept)}.",
                )

    @staticmethod
    def _reference() -> str:
        return f"INC-{datetime.now(UTC):%Y%m%d}-{secrets.token_hex(3)}"

    @classmethod
    async def _commit_attachments(
        cls,
        attachments: list[UploadFile],
        reference: str,
        client: GitHubIssueClient,
    ) -> dict[str, str]:
        urls: dict[str, str] = {}
        for attachment in attachments:
            name = cls._safe_filename(attachment.filename, len(urls))
            urls[name] = await client.commit_attachment(
                path=f"attachments/{reference}/{name}",
                content=await attachment.read(),
                message=f"Attach {name} to {reference}",
            )
        return urls

    @staticmethod
    def _safe_filename(filename: str | None, index: int) -> str:
        """A reporter's filename becomes a path in a git repository, so it cannot be trusted.

        Taking the basename and allowing only a known character set removes both directory
        traversal and the shell-hostile names that a screenshot tool sometimes produces.
        """
        candidate = (filename or "").replace("\\", "/").rsplit("/", 1)[-1]
        cleaned = UNSAFE_IN_FILENAME.sub("-", candidate).strip("-.")
        return cleaned[:MAX_FILENAME_LENGTH] or f"attachment-{index + 1}"
