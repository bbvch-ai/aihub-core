from datetime import UTC, datetime
from typing import Any

from swiss_ai_hub.pipeline.resources.confluence.tests.fake_confluence import FakeConfluence
from swiss_ai_hub.pipeline.source_pipelines.confluence.confluence_page import ConfluencePage
from swiss_ai_hub.pipeline.types.markdown_frontmatter import MarkdownFrontmatter


def _page(page_id: str = "42", title: str = "Deploy guide", **changes: Any) -> dict[str, Any]:
    fake = FakeConfluence()
    values = {
        "ancestors": [("1", "Engineering"), ("7", "Runbooks")],
        "labels": ["runbook", "backend"],
        "body": "<h2>Steps</h2><p>Run make deploy.</p>",
        **changes,
    }
    return fake.add_page(page_id, title, **values)


def _summary(page: dict[str, Any]) -> dict[str, Any]:
    """What the listing reads: the search result without body, history or labels."""
    return {key: value for key, value in page.items() if key not in ("body", "history", "metadata")}


class TestRecordFile:
    def test_a_page_lives_under_its_space_and_the_titles_above_it(self):
        assert ConfluencePage.from_result(_page()).to_record_file().object_key == (
            "ENG/Engineering/Runbooks/Deploy guide.md"
        )

    def test_the_listing_names_the_same_file_from_a_summary(self):
        """A listed key the sync never writes would have the reconcile step delete data."""
        page = _page()

        assert (
            ConfluencePage.object_key_of(_summary(page)) == ConfluencePage.from_result(page).to_record_file().object_key
        )

    def test_every_frontmatter_field_reaches_the_document_and_none_is_skipped(self):
        rendered = ConfluencePage.from_result(_page()).to_record_file().render().decode()

        frontmatter = MarkdownFrontmatter.from_markdown(rendered)

        assert frontmatter.skipped == {}
        assert (frontmatter.title, frontmatter.url) == (
            "Deploy guide",
            "https://acme.atlassian.net/wiki/spaces/ENG/pages/42",
        )
        assert frontmatter.created == int(datetime(2026, 9, 1, 8, tzinfo=UTC).timestamp())
        assert frontmatter.metadata == {
            "ancestors": ["Engineering", "Runbooks"],
            "author": "Ada Lovelace",
            "labels": ["backend", "runbook"],
            "page_id": "42",
            "page_version": 1,
            "space": "ENG",
            "updated": "2026-10-01T09:00:00.000Z",
        }

    def test_the_body_opens_with_the_title_and_holds_the_page(self):
        body = ConfluencePage.from_result(_page()).to_record_file().body

        assert body == "# Deploy guide\n\n## Steps\n\nRun make deploy."

    def test_a_page_without_text_still_has_its_title(self):
        assert ConfluencePage.from_result(_page(body="")).to_record_file().body == "# Deploy guide"

    def test_a_root_page_has_no_ancestors_in_its_frontmatter(self):
        file = ConfluencePage.from_result(_page(ancestors=[], labels=[])).to_record_file()

        assert file.object_key == "ENG/Deploy guide.md"
        assert "ancestors" not in file.frontmatter or file.frontmatter["ancestors"] is None
        assert "ancestors:" not in file.render().decode()

    def test_a_title_of_dots_alone_is_written_under_the_page_id(self):
        """Such a title cannot be a folder or a file name, and would fail every sync of the database."""
        page = _page(page_id="9", title="..", ancestors=[("1", "...")])

        assert ConfluencePage.from_result(page).to_record_file().object_key == "ENG/page 1/page 9.md"
        assert ConfluencePage.object_key_of(_summary(page)) == "ENG/page 1/page 9.md"
