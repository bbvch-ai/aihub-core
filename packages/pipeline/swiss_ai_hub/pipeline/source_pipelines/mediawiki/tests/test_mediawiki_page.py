import pytest

from swiss_ai_hub.pipeline.source_pipelines.mediawiki.mediawiki_page import MediaWikiPage

_URL = "https://wiki.acme.test/index.php/Process:Onboarding/Laptop"


def _listed(title: str, namespace: int = 0, page_id: int = 7) -> dict:
    return {"pageid": page_id, "ns": namespace, "title": title, "lastrevid": 42, "canonicalurl": _URL}


def _page(**changes: object) -> MediaWikiPage:
    parsed = {
        "revid": 42,
        "text": '<p>See <a href="/index.php/Main_Page">the main page</a>.</p>',
        "categories": [
            {"category": "Onboarding_guides"},
            {"category": "Pages_with_broken_file_links", "hidden": True},
        ],
    }
    return MediaWikiPage.from_parse(
        _listed("Process:Onboarding/Laptop", namespace=100),
        {**parsed, **changes},
        "Process",
        created="2014-11-28T13:14:45Z",
        updated="2026-10-02T08:00:00Z",
    )


class TestPath:
    def test_a_main_namespace_title_is_the_file_name(self):
        assert MediaWikiPage.object_key_of(_listed("Welcome"), "Main") == "Main/Welcome.md"

    def test_the_namespace_prefix_is_dropped_and_subpages_become_folders(self):
        page = _listed("Process:Onboarding/Laptop", namespace=100)

        assert MediaWikiPage.object_key_of(page, "Process") == "Process/Onboarding/Laptop.md"

    def test_only_the_first_colon_separates_the_namespace(self):
        page = _listed("Process:Release: 2026", namespace=100)

        assert MediaWikiPage.object_key_of(page, "Process") == "Process/Release: 2026.md"

    @pytest.mark.parametrize(
        ("title", "key"),
        [("AC/", "Main/AC_.md"), ("../etc", "Main/.._etc.md"), ("...", "Main/page 7.md"), ("/", "Main/page 7.md")],
    )
    def test_a_title_that_would_give_an_empty_or_relative_folder_stays_one_file(self, title: str, key: str):
        assert MediaWikiPage.object_key_of(_listed(title), "Main") == key


class TestRecordFile:
    def test_the_file_carries_the_page_with_links_made_absolute(self):
        record = _page().to_record_file()

        assert record.object_key == "Process/Onboarding/Laptop.md"
        assert record.frontmatter == {
            "title": "Process:Onboarding/Laptop",
            "url": _URL,
            "created": "2014-11-28T13:14:45Z",
            "updated": "2026-10-02T08:00:00Z",
            "page_id": 7,
            "revision": 42,
            "categories": ["Onboarding guides"],
        }
        assert record.body == (
            "# Process:Onboarding/Laptop\n\nSee [the main page](https://wiki.acme.test/index.php/Main_Page)."
        )

    def test_a_page_without_text_is_its_title(self):
        record = _page(text="", categories=[]).to_record_file()

        assert record.body == "# Process:Onboarding/Laptop"
        assert "categories" not in record.render().decode()

    def test_the_record_survives_the_round_trip_through_dlt(self):
        """The sync yields dumped pages; the destination rebuilds the file from the dump."""
        page = _page()

        assert MediaWikiPage.model_validate(page.model_dump()).to_record_file() == page.to_record_file()
