import json
from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile
from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.incident import IncidentContext, IncidentSettings

from swiss_ai_hub.api.routes.incident.incident_service import INCIDENT_FORM, IncidentService

VALID = {
    "what_went_wrong": "Chat returns nothing",
    "problem_type": "Error or no response",
    "impact": "I can't continue",
    "frequency": "Every time",
    "occurred_at": "2026-09-18 02:10",
    "tenant": "Acme (68c1)",
    "version": "0.322.0",
    "reporter_email": "admin@your-company.com",
}


class _RecordingClient:
    def __init__(self):
        self.committed: list[tuple[str, bytes]] = []
        self.issue: dict | None = None

    async def ensure_repository_is_private(self) -> None:
        return None

    async def commit_attachment(self, path: str, content: bytes, message: str) -> str:
        self.committed.append((path, content))
        return f"https://example.test/{path}"

    async def create_issue(self, title: str, body: str, labels: list[str]) -> dict:
        self.issue = {"title": title, "body": body, "labels": labels}
        return {"number": 42}


def _upload(filename: str, content: bytes = b"x") -> UploadFile:
    return UploadFile(filename=filename, file=BytesIO(content), size=len(content))


def _user() -> UserIdentity:
    return UserIdentity(
        id="u1",
        name="Admin User",
        email="admin@your-company.com",
        roles=[],
        acting_within_tenant=TenantIdentity(id="68c1", name="Acme", access_rules=[]),
    )


async def _create(submission: dict, attachments: list[UploadFile], client, **setting_overrides):
    return await IncidentService.create(
        user=_user(),
        submission_json=json.dumps(submission),
        attachments=attachments,
        client=client,
        settings=IncidentSettings(GITHUB_REPOSITORY="o/r", GITHUB_APP_ID="1", **setting_overrides),
    )


def test_should_prefill_only_the_questions_the_platform_knows() -> None:
    form = IncidentService.form(IncidentContext(tenant="Acme (68c1)", reporter_name="Admin User"))

    by_name = {getattr(element, "name", None): element for element in form.elements}
    assert by_name["tenant"].value == "Acme (68c1)"
    assert by_name["reporter_name"].value == "Admin User"
    assert by_name["what_went_wrong"].value is None


def test_should_publish_the_submission_schema_alongside_the_elements() -> None:
    form = IncidentService.form(IncidentContext())

    assert "what_went_wrong" in form.submission_specs["required"]
    assert "page_url" not in form.submission_specs.get("required", [])


@pytest.mark.asyncio
async def test_should_file_an_issue_and_report_its_number() -> None:
    client = _RecordingClient()

    created = await _create(VALID, [], client)

    assert created.number == 42
    assert created.reference.startswith("INC-")
    assert client.issue["labels"] == INCIDENT_FORM.labels


@pytest.mark.asyncio
async def test_should_reject_a_submission_that_is_not_json() -> None:
    with pytest.raises(HTTPException) as rejected:
        await IncidentService.create(
            user=_user(),
            submission_json="{not json",
            attachments=[],
            client=_RecordingClient(),
            settings=IncidentSettings(),
        )

    assert rejected.value.status_code == 422


@pytest.mark.asyncio
async def test_should_reject_a_submission_missing_a_required_answer() -> None:
    incomplete = {key: value for key, value in VALID.items() if key != "what_went_wrong"}

    with pytest.raises(HTTPException) as rejected:
        await _create(incomplete, [], _RecordingClient())

    assert rejected.value.status_code == 422


@pytest.mark.asyncio
async def test_should_reject_a_dropdown_answer_the_form_does_not_offer() -> None:
    with pytest.raises(HTTPException) as rejected:
        await _create(VALID | {"impact": "Catastrophic"}, [], _RecordingClient())

    assert rejected.value.status_code == 422


@pytest.mark.asyncio
async def test_should_reject_more_attachments_than_allowed() -> None:
    attachments = [_upload(f"{index}.png") for index in range(3)]

    with pytest.raises(HTTPException) as rejected:
        await _create(VALID, attachments, _RecordingClient(), MAX_ATTACHMENTS=2)

    assert rejected.value.status_code == 413


@pytest.mark.asyncio
async def test_should_reject_an_attachment_over_the_size_limit() -> None:
    with pytest.raises(HTTPException) as rejected:
        await _create(VALID, [_upload("big.png", b"0" * 100)], _RecordingClient(), MAX_ATTACHMENT_BYTES=10)

    assert rejected.value.status_code == 413


@pytest.mark.asyncio
async def test_should_commit_attachments_under_the_report_reference() -> None:
    client = _RecordingClient()

    created = await _create(VALID, [_upload("shot.png", b"png")], client)

    path, content = client.committed[0]
    assert path == f"attachments/{created.reference}/shot.png"
    assert content == b"png"
    assert created.attachments == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("../../../etc/passwd", "passwd"),
        ("C:\\Users\\me\\shot.png", "shot.png"),
        ("../../secrets.env", "secrets.env"),
        ("sub/dir/report.pdf", "report.pdf"),
        ("naughty;$(whoami).png", "naughty-whoami-.png"),
    ],
)
async def test_should_never_let_a_filename_escape_the_attachment_directory(filename: str, expected: str) -> None:
    """A reporter's filename becomes a path in a git repository, so traversal has to be impossible."""
    client = _RecordingClient()

    created = await _create(VALID, [_upload(filename)], client)

    path, _ = client.committed[0]
    assert path == f"attachments/{created.reference}/{expected}"
    assert ".." not in path


@pytest.mark.asyncio
async def test_should_name_an_attachment_that_arrived_without_a_usable_filename() -> None:
    client = _RecordingClient()

    created = await _create(VALID, [_upload("...")], client)

    assert client.committed[0][0] == f"attachments/{created.reference}/attachment-1"


@pytest.mark.asyncio
async def test_should_check_the_repository_is_private_before_writing_anything() -> None:
    class _PublicRepository(_RecordingClient):
        async def ensure_repository_is_private(self) -> None:
            raise PermissionError("Incident repository o/r is public.")

    client = _PublicRepository()

    with pytest.raises(PermissionError):
        await _create(VALID, [_upload("shot.png")], client)

    assert client.committed == [], "nothing may be committed to a public repository"
    assert client.issue is None
