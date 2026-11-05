import yaml

from swiss_ai_hub.pipeline.resources.jira.tests.fake_jira import FakeJira
from swiss_ai_hub.pipeline.source_pipelines.jira.jira_comment import JiraComment
from swiss_ai_hub.pipeline.source_pipelines.jira.jira_issue import JiraIssue


def _issue(hit: dict) -> JiraIssue:
    return JiraIssue.from_search_hit(hit, JiraComment.from_embedded(hit))


def _frontmatter_and_body(issue: JiraIssue) -> tuple[dict, str]:
    _, header, body = issue.to_record_file().render().decode().split("---\n", 2)
    return yaml.safe_load(header), body.strip()


class TestFile:
    def test_an_issue_is_written_under_its_project_named_after_its_key(self):
        hit = FakeJira().add_issue("ABC-12")

        assert _issue(hit).to_record_file().object_key == "ABC/ABC-12.md"
        assert JiraIssue.object_key_for("ABC-12") == "ABC/ABC-12.md"

    def test_the_frontmatter_carries_the_fields_a_retriever_filters_on(self):
        hit = FakeJira().add_issue(
            "ABC-12",
            summary="Login fails",
            issuetype={"name": "Bug"},
            status={"name": "In Progress"},
            priority={"name": "High"},
            labels=["backend", "auth"],
            components=[{"name": "API"}],
            fixVersions=[{"name": "1.2"}],
            assignee={"displayName": "Ada Assignee", "emailAddress": "ada@acme.test"},
        )

        frontmatter, _ = _frontmatter_and_body(_issue(hit))

        assert frontmatter == {
            "title": "ABC-12: Login fails",
            "url": "https://acme.atlassian.net/browse/ABC-12",
            "created": "2026-10-01T07:00:00Z",
            "updated": "2026-10-02T08:30:00Z",
            "key": "ABC-12",
            "project": "ABC",
            "issue_type": "Bug",
            "status": "In Progress",
            "priority": "High",
            "labels": ["auth", "backend"],
            "components": ["API"],
            "fix_versions": ["1.2"],
            "reporter": "Rita Reporter",
            "assignee": "Ada Assignee",
        }

    def test_no_email_address_reaches_the_file(self):
        hit = FakeJira().add_issue("ABC-1", assignee={"displayName": "Ada", "emailAddress": "ada@acme.test"})

        assert b"@acme.test" not in _issue(hit).to_record_file().render()

    def test_empty_fields_are_left_out(self):
        hit = FakeJira().add_issue("ABC-1", priority=None, labels=[], assignee=None)

        frontmatter, _ = _frontmatter_and_body(_issue(hit))

        assert {"priority", "labels", "components", "fix_versions", "assignee"}.isdisjoint(frontmatter)

    def test_the_body_holds_the_description_and_every_public_comment_oldest_first(self):
        hit = FakeJira().add_issue("ABC-1", comments=2)

        _, body = _frontmatter_and_body(_issue(hit))

        assert body == (
            "# ABC-1: Summary of ABC-1\n\n"
            "## Description\n\nDescription of ABC-1\n\n"
            "## Comments\n\n"
            "### Commenter 1 · 2026-10-03 07:00 UTC\n\nComment 1\n\n"
            "### Commenter 2 · 2026-10-03 08:00 UTC\n\nComment 2"
        )

    def test_an_issue_without_description_or_comments_has_only_its_title(self):
        hit = FakeJira().add_issue("ABC-1")
        hit["renderedFields"]["description"] = None

        _, body = _frontmatter_and_body(_issue(hit))

        assert body == "# ABC-1: Summary of ABC-1"

    def test_unicode_survives(self):
        hit = FakeJira().add_issue("ABC-1", summary="Größe prüfen – 日本語")

        frontmatter, body = _frontmatter_and_body(_issue(hit))

        assert frontmatter["title"] == "ABC-1: Größe prüfen – 日本語"
        assert body.startswith("# ABC-1: Größe prüfen – 日本語")

    def test_a_data_center_context_path_is_part_of_the_link(self):
        hit = FakeJira(site="https://jira.acme.ch/jira").add_issue("ABC-1")

        assert _issue(hit).to_record_file().frontmatter["url"] == "https://jira.acme.ch/jira/browse/ABC-1"

    def test_the_same_issue_renders_to_the_same_bytes(self):
        """An unchanged issue must be skipped by the ETag check, on every run."""
        first = _issue(FakeJira().add_issue("ABC-1", comments=3)).to_record_file().render()
        second = _issue(FakeJira().add_issue("ABC-1", comments=3)).to_record_file().render()

        assert first == second

    def test_the_record_round_trips_through_a_plain_dict(self):
        """dlt hands the adapter the yielded dict, not the model."""
        issue = _issue(FakeJira().add_issue("ABC-1", comments=1))

        assert JiraIssue.model_validate(issue.model_dump()) == issue


class TestComments:
    def test_restricted_comments_are_left_out(self):
        """A comment limited to a role or group, or an internal service desk comment, is not for every reader."""
        hit = FakeJira().add_issue("ABC-1", comments=3)
        hit["fields"]["comment"]["comments"][0]["visibility"] = {"type": "role", "value": "Developers"}
        hit["fields"]["comment"]["comments"][1]["jsdPublic"] = False

        assert [comment.id for comment in JiraComment.from_embedded(hit)] == ["3"]

    def test_comments_beyond_the_embedded_ones_need_the_comment_endpoint(self):
        hit = FakeJira().add_issue("ABC-1", comments=25)
        hit["fields"]["comment"]["comments"] = hit["fields"]["comment"]["comments"][:20]

        assert JiraComment.has_more_than_embedded(hit)
        assert not JiraComment.has_more_than_embedded(FakeJira().add_issue("ABC-2", comments=3))

    def test_paged_comments_use_their_rendered_body(self):
        raw = [
            {
                "id": "7",
                "author": {"displayName": "Bo"},
                "created": "2026-10-03T10:00:00.000+0000",
                "renderedBody": "<b>x</b>",
            }
        ]

        [comment] = JiraComment.from_paged(raw)

        assert (comment.author, comment.created, comment.body_html) == ("Bo", "2026-10-03T10:00:00Z", "<b>x</b>")

    def test_an_internal_comment_is_recognised_by_its_property(self):
        """Data Center marks an internal service desk comment only with the ``sd.public.comment`` property."""
        internal = {"key": "sd.public.comment", "value": {"internal": True}}
        public = {"key": "sd.public.comment", "value": {"internal": False}}
        raw = [
            {
                "id": "1",
                "author": {"displayName": "A"},
                "created": "2026-10-03T10:00:00.000+0000",
                "properties": [public],
            },
            {
                "id": "2",
                "author": {"displayName": "B"},
                "created": "2026-10-03T11:00:00.000+0000",
                "properties": [internal],
            },
        ]

        assert [comment.id for comment in JiraComment.from_paged(raw)] == ["1"]

    def test_a_deleted_author_still_gives_a_heading(self):
        [comment] = JiraComment.from_paged([{"id": "1", "author": None, "created": "2026-10-03T10:00:00.000+0000"}])

        assert comment.author == "Unknown"
