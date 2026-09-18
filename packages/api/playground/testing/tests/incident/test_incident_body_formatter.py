from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.incident import IssueFormParser

from swiss_ai_hub.api.routes.incident.incident_body_formatter import IncidentBodyFormatter

DEFINITION = """
title: '[INC] '
body:
  - type: markdown
    attributes:
      value: ignore me
  - type: textarea
    id: what_went_wrong
    attributes:
      label: What went wrong?
    validations:
      required: true
  - type: dropdown
    id: impact
    attributes:
      label: Impact
      options: [High, Low]
  - type: textarea
    id: logs
    attributes:
      label: Logs
      render: shell
  - type: input
    id: tenant
    attributes:
      label: Tenant
"""

FORM = IssueFormParser.parse(DEFINITION)


def _user(tenant: TenantIdentity | None = None) -> UserIdentity:
    return UserIdentity(
        id="user-1",
        name="Admin User",
        email="admin@your-company.com",
        roles=[],
        acting_within_tenant=tenant,
    )


def test_should_write_one_heading_per_question_in_definition_order() -> None:
    body = IncidentBodyFormatter.body(FORM, {"what_went_wrong": "It broke"}, _user(), {})

    assert body.index("### What went wrong?") < body.index("### Impact") < body.index("### Tenant")


def test_should_mark_an_unanswered_question_the_way_github_does() -> None:
    body = IncidentBodyFormatter.body(FORM, {"what_went_wrong": "It broke"}, _user(), {})

    assert "### Impact\n\n_No response_" in body


def test_should_wrap_an_answer_in_a_code_fence_when_the_form_asks_for_one() -> None:
    body = IncidentBodyFormatter.body(FORM, {"what_went_wrong": "x", "logs": "traceback"}, _user(), {})

    assert "### Logs\n\n```shell\ntraceback\n```" in body


def test_should_join_a_multi_value_answer() -> None:
    body = IncidentBodyFormatter.body(FORM, {"what_went_wrong": "x", "impact": ["High", "Low"]}, _user(), {})

    assert "### Impact\n\nHigh, Low" in body


def test_should_embed_an_image_attachment_and_link_everything_else() -> None:
    attachments = {"shot.png": "https://example.test/shot.png", "log.txt": "https://example.test/log.txt"}

    body = IncidentBodyFormatter.body(FORM, {"what_went_wrong": "x"}, _user(), attachments)

    assert "![shot.png](https://example.test/shot.png)" in body
    assert "[log.txt](https://example.test/log.txt)" in body
    assert "![log.txt]" not in body


def test_should_omit_the_attachment_section_when_there_are_none() -> None:
    body = IncidentBodyFormatter.body(FORM, {"what_went_wrong": "x"}, _user(), {})

    assert "### Attachments" not in body


def test_should_take_reporter_identity_from_the_token_not_the_submission() -> None:
    """Every answer is editable, so identity has to come from somewhere the reporter cannot reach."""
    submission = {"what_went_wrong": "x", "tenant": "Someone Else's Tenant"}

    body = IncidentBodyFormatter.body(
        FORM, submission, _user(TenantIdentity(id="68c1", name="Acme", access_rules=[])), {}
    )

    verified = body.split("<details><summary>Verified by AI Hub</summary>")[1]
    assert "Admin User <admin@your-company.com>" in verified
    assert "Acme (68c1)" in verified
    assert "Someone Else's Tenant" not in verified


def test_should_say_so_when_no_tenant_resolved_rather_than_inventing_one() -> None:
    body = IncidentBodyFormatter.body(FORM, {"what_went_wrong": "x"}, _user(), {})

    assert "- Tenant: not resolved" in body


def test_should_title_the_issue_from_the_first_free_text_answer() -> None:
    title = IncidentBodyFormatter.title(FORM, {"what_went_wrong": "Chat  returns\nnothing at all"})

    assert title == "[INC] Chat returns nothing at all"


def test_should_shorten_a_long_summary_so_the_issue_list_stays_readable() -> None:
    title = IncidentBodyFormatter.title(FORM, {"what_went_wrong": "word " * 40})

    assert len(title) <= len("[INC] ") + 60
    assert title.endswith("…")


def test_should_fall_back_to_a_generic_title_when_the_summary_is_empty() -> None:
    title = IncidentBodyFormatter.title(FORM, {})

    assert title == "[INC] Incident report"
