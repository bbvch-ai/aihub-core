from typing import Annotated

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.incident import IssueForm

NO_ANSWER = "_No response_"
TITLE_LENGTH = 60


class IncidentBodyFormatter:
    """Renders a submission the way GitHub renders its own issue forms.

    Same `### Label` headings, same `_No response_` for a skipped question — so an issue that
    arrived through AI Hub is indistinguishable from one typed on github.com, and nobody
    triaging has to learn a second layout.
    """

    @classmethod
    def title(
        cls,
        form: Annotated[IssueForm, "Parsed form"],
        submission: Annotated[dict, "Validated answers"],
    ) -> str:
        """First answer, trimmed — the summary a reader scans in the issue list.

        The form's own `title` value is the prefix GitHub would have pre-filled.
        """
        first = next((field.id for field in form.fields if field.type == "textarea"), None)
        summary = " ".join(str(submission.get(first) or "").split()) if first else ""
        if len(summary) > TITLE_LENGTH:
            summary = summary[: TITLE_LENGTH - 1].rstrip() + "…"
        return f"{form.title_prefix}{summary or 'Incident report'}"

    @classmethod
    def body(
        cls,
        form: Annotated[IssueForm, "Parsed form"],
        submission: Annotated[dict, "Validated answers"],
        user: Annotated[UserIdentity, "Authenticated reporter, from the token"],
        attachment_urls: Annotated[dict[str, str], "Committed attachment name to URL"],
    ) -> str:
        sections = [
            cls._section(field.label, cls._answer(field.render, submission.get(field.id))) for field in form.fields
        ]
        if attachment_urls:
            sections.append(cls._section("Attachments", cls._attachments(attachment_urls)))
        sections.append(cls._verified(user))
        return "\n\n".join(sections)

    @staticmethod
    def _section(label: str, value: str) -> str:
        return f"### {label}\n\n{value}"

    @staticmethod
    def _answer(render: str | None, value: object) -> str:
        if value is None or value == "" or value == []:
            return NO_ANSWER
        text = ", ".join(str(item) for item in value) if isinstance(value, list) else str(value)
        return f"```{render}\n{text}\n```" if render else text

    @staticmethod
    def _attachments(attachment_urls: dict[str, str]) -> str:
        """Linked, never embedded — including screenshots.

        Embedding needs a URL that serves the bytes, and a private repository has no such URL
        that lasts: `raw.githubusercontent.com` refuses anonymous requests (404) and the tokened
        form the contents API hands back expires. A link to the file's page in the repository
        always resolves for whoever can read the repository, which is exactly the audience.
        """
        return "\n".join(f"[{name}]({url})" for name, url in attachment_urls.items())

    @staticmethod
    def _verified(user: UserIdentity) -> str:
        """The two facts taken from the token rather than the form.

        Every answer above is prefilled but editable, so none of it can be trusted as identity.
        Whoever triages the report needs to know which account actually sent it — a report
        attributed to the wrong person or tenant sends the investigation to the wrong place.
        """
        tenant = user.acting_within_tenant
        tenant_line = f"{tenant.name} ({tenant.id})" if tenant else "not resolved"
        return (
            "<details><summary>Verified by AI Hub</summary>\n\n"
            f"- Reporter: {user.name} <{user.email}>\n"
            f"- Tenant: {tenant_line}\n"
            "\n</details>"
        )
