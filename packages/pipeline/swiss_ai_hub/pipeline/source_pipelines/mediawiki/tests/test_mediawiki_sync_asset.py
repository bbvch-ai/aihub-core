"""Real syncs of the shipped structured asset against a fake MediaWiki, run after run, as the daily schedule does."""

from collections import Counter
from unittest.mock import MagicMock
from urllib.parse import parse_qs, unquote, urlsplit

import pytest
from dagster import AssetKey
from swiss_ai_hub.core.network import SourceHostGuard

from swiss_ai_hub.pipeline.assets.factories.structured_to_data_lake.structured_sync_factory import (
    structured_sync_factory,
)
from swiss_ai_hub.pipeline.ops.structured.tests.test_structured_sync_asset import World
from swiss_ai_hub.pipeline.resources.mediawiki.tests.fake_mediawiki import SITE, FakeMediaWiki
from swiss_ai_hub.pipeline.source_pipelines.structured_sync_config import StructuredSyncConfig

_ASSET = structured_sync_factory(
    AssetKey(["structured_source_to_datalake", "records"]), source="structured", config_type=StructuredSyncConfig
)
_FILES = [
    "Main/Onboarding.md",
    "Main/Onboarding/Laptop.md",
    "Main/Welcome.md",
    "Process/Release.md",
]


@pytest.fixture(autouse=True)
def external_site(monkeypatch: pytest.MonkeyPatch) -> None:
    """The fake site's name must never reach a real resolver; the guard has tests of its own."""
    monkeypatch.setattr(SourceHostGuard, "require_public", lambda url, allowed_hosts, allow_list_variable: None)


@pytest.fixture
def wiki(world: World, monkeypatch: pytest.MonkeyPatch) -> FakeMediaWiki:
    fake = FakeMediaWiki(page_size=2)
    fake.pluggable_auth = True
    fake.add_page(1, "Welcome", html="<p>Hello <b>team</b></p>", categories=["Onboarding"])
    fake.add_page(2, "Onboarding")
    fake.add_page(3, "Onboarding/Laptop")
    fake.add_page(4, "Lunch menu", categories=["Hide From AI"])
    fake.add_page(10, "Release", namespace=100)
    fake.add_page(20, "Old process", namespace=4)
    fake.install(monkeypatch)
    _configure(world)
    world.rows["wiki-db"] = MagicMock(source="structured", deleting=False)
    return fake


def _configure(world: World, **changes: object) -> None:
    options = {
        "base_url": SITE,
        "auth_method": "web_form",
        "username": "Sync bot",
        "password": "form-secret",
        "namespaces": ["Main", "Process"],
        "exclude_categories": ["Hide From AI"],
        **changes,
    }
    world.configs["wiki-db"] = StructuredSyncConfig.model_validate({"source_kind": "mediawiki", "mediawiki": options})


class TestMediaWikiSync:
    def test_a_first_sync_writes_every_page_in_scope_with_subpages_as_folders(self, world: World, wiki: FakeMediaWiki):
        result = world.sync("wiki-db", asset=_ASSET)

        assert result.success
        assert world.files("wiki-db") == _FILES
        welcome = world.body("wiki-db", "Main/Welcome.md")
        assert "url: https://wiki.acme.test/index.php/Welcome\n" in welcome
        assert "created: '2026-10-01T08:00:00Z'\n" in welcome
        assert "\n# Welcome\n\nHello **team**\n" in welcome

    def test_a_second_sync_of_unchanged_pages_renders_nothing_and_writes_nothing(
        self, world: World, wiki: FakeMediaWiki
    ):
        world.sync("wiki-db", asset=_ASSET)
        writes, parses = world.file_writes(), len(wiki.parses())

        result = world.sync("wiki-db", asset=_ASSET)

        assert result.success
        assert world.file_writes() == writes
        assert wiki.parses()[parses:] == []
        assert world.step_metadata(result, "sync_structured_records")["Files written"] == 0

    def test_an_edited_page_is_the_only_one_rendered_and_rewritten(self, world: World, wiki: FakeMediaWiki):
        world.sync("wiki-db", asset=_ASSET)
        writes, parses = world.file_writes(), len(wiki.parses())
        wiki.edit(3, "<p>Ask IT for a laptop.</p>")

        assert world.sync("wiki-db", asset=_ASSET).success

        assert wiki.parses()[parses:] == [3]
        assert world.file_writes() == writes + 1
        assert "Ask IT for a laptop." in world.body("wiki-db", "Main/Onboarding/Laptop.md")

    def test_a_renamed_page_moves_its_file_and_leaves_no_stale_one(self, world: World, wiki: FakeMediaWiki):
        """A move keeps the page's revision; only its path tells the sync that it changed."""
        world.sync("wiki-db", asset=_ASSET)
        wiki.rename(1, "Hello")

        assert world.sync("wiki-db", asset=_ASSET).success

        assert "Main/Hello.md" in world.files("wiki-db")
        assert "Main/Welcome.md" not in world.files("wiki-db")
        assert world.announced(world.removed_events) == ["Main/Welcome.md"]

    def test_a_page_put_in_an_excluded_category_is_removed_without_a_new_revision(
        self, world: World, wiki: FakeMediaWiki
    ):
        """A template edit can put a page in a category without giving the page itself a revision."""
        world.sync("wiki-db", asset=_ASSET)
        wiki.categorize(2, ["Hide From AI"])

        assert world.sync("wiki-db", asset=_ASSET).success

        assert "Main/Onboarding.md" not in world.files("wiki-db")

    def test_a_page_taken_out_of_an_excluded_category_is_read_again(self, world: World, wiki: FakeMediaWiki):
        wiki.category_pages.add("Hide From AI")
        world.sync("wiki-db", asset=_ASSET)
        parses = len(wiki.parses())
        wiki.categorize(4, [])

        assert world.sync("wiki-db", asset=_ASSET).success

        assert wiki.parses()[parses:] == [4]
        assert "Main/Lunch menu.md" in world.files("wiki-db")

    def test_a_deleted_page_is_removed(self, world: World, wiki: FakeMediaWiki):
        world.sync("wiki-db", asset=_ASSET)
        wiki.remove(10)

        assert world.sync("wiki-db", asset=_ASSET).success

        assert "Process/Release.md" not in world.files("wiki-db")
        assert world.announced(world.removed_events) == ["Process/Release.md"]

    def test_included_categories_narrow_the_scope(self, world: World, wiki: FakeMediaWiki):
        _configure(world, include_categories=["Onboarding"])

        assert world.sync("wiki-db", asset=_ASSET).success

        assert world.files("wiki-db") == ["Main/Welcome.md"]

    def test_a_refused_sign_in_fails_the_sync_and_removes_nothing(self, world: World, wiki: FakeMediaWiki):
        world.sync("wiki-db", asset=_ASSET)
        wiki.accounts["Sync bot"] = "rotated"
        wiki.signed_in_as = None

        result = world.sync("wiki-db", asset=_ASSET)

        assert not result.success
        [failure] = result.get_step_failure_events()
        shown_on_the_run_page = failure.event_specific_data.error.to_string()
        assert "refused the user name or password of Sync bot" in shown_on_the_run_page
        assert "form-secret" not in shown_on_the_run_page
        assert world.files("wiki-db") == _FILES

    def test_an_oauth_token_syncs_the_same_pages(self, world: World, wiki: FakeMediaWiki):
        _configure(world, auth_method="oauth", username="", password="", access_token="oauth-secret")

        assert world.sync("wiki-db", asset=_ASSET).success

        assert world.files("wiki-db") == _FILES
        assert all("Bearer oauth-secret" == request.headers.get("Authorization") for request in wiki.requests)

    def test_two_titles_sharing_a_path_keep_the_first_listed_page_in_sync_and_listing(
        self, world: World, wiki: FakeMediaWiki
    ):
        """A//B and A__B are both stored as Main/A__B.md. The first one listed keeps it, however the ids sort, and an
        edit of the other one does not take it over."""
        wiki.add_page(1000, "A//B", html="<p>First listed</p>")
        wiki.add_page(900, "A__B", html="<p>Listed second</p>")
        world.sync("wiki-db", asset=_ASSET)
        wiki.edit(900, "<p>Listed second, edited</p>")

        assert world.sync("wiki-db", asset=_ASSET).success

        assert "First listed" in world.body("wiki-db", "Main/A__B.md")
        assert 900 not in wiki.parses()

    def test_each_namespace_is_listed_once_per_step(self, world: World, wiki: FakeMediaWiki):
        """The pages, their files and the listing step all work from one listing of the pages."""
        _configure(world, sync_documents=True, sync_images=True)

        assert world.sync("wiki-db", asset=_ASSET).success

        first_pages = [
            query
            for request in wiki.requests
            if (query := parse_qs(urlsplit(request.url or "").query)).get("generator") == ["allpages"]
            and "gapcontinue" not in query
        ]
        listed = Counter(query["gapnamespace"][0] for query in first_pages)
        assert listed == {"0": 2, "100": 2, "10": 2}

    def test_an_excluded_category_reaches_its_subcategories_when_asked(self, world: World, wiki: FakeMediaWiki):
        wiki.add_page(30, "Hide From AI/Drafts", namespace=14, categories=["Hide From AI"])
        wiki.categorize(3, ["Hide From AI/Drafts"])

        assert world.sync("wiki-db", asset=_ASSET).success
        assert "Main/Onboarding/Laptop.md" in world.files("wiki-db")

        _configure(world, include_subcategories=True)
        assert world.sync("wiki-db", asset=_ASSET).success
        assert "Main/Onboarding/Laptop.md" not in world.files("wiki-db")

    def test_adding_a_namespace_reads_everything_again(self, world: World, wiki: FakeMediaWiki):
        world.sync("wiki-db", asset=_ASSET)
        parses = len(wiki.parses())
        _configure(world, namespaces=["Main", "Process", "Project"])

        assert world.sync("wiki-db", asset=_ASSET).success

        assert sorted(wiki.parses()[parses:]) == [1, 2, 3, 10, 20]
        assert "Project/Old process.md" in world.files("wiki-db")


class TestFileSync:
    @pytest.fixture
    def files(self, world: World, wiki: FakeMediaWiki) -> FakeMediaWiki:
        """A wiki whose pages use documents, images and files nobody should see."""
        wiki.add_file(101, "Handbook 2026.pdf", b"%PDF-1.7 handbook", used_by=[1, 2])
        wiki.add_file(102, "Rollout.pptx", b"PK pptx", used_by=[10])
        wiki.add_file(103, "Team photo.jpg", b"JPEG", used_by=[1])
        wiki.add_file(104, "Old minutes.doc", b"DOC", used_by=[2])
        wiki.add_file(105, "Menu.pdf", b"%PDF-1.7 menu", used_by=[4])
        wiki.add_file(106, "Salaries.pdf", b"%PDF-1.7 salaries", used_by=[1], categories=["Hide From AI"])
        wiki.add_file(107, "Logo.pdf", b"%PDF-1.7 commons", used_by=[1], repository="shared")
        wiki.category_pages.add("Hide From AI")
        _configure(world, sync_documents=True)
        return wiki

    def test_files_are_not_synced_unless_switched_on(self, world: World, wiki: FakeMediaWiki):
        wiki.add_file(101, "Handbook 2026.pdf", b"%PDF-1.7 handbook", used_by=[1])

        assert world.sync("wiki-db", asset=_ASSET).success

        assert world.files("wiki-db") == _FILES
        assert wiki.downloads == []

    def test_only_documents_of_synced_pages_land_in_the_file_collection(self, world: World, files: FakeMediaWiki):
        """Images, old Office formats, files used only on excluded pages, files in an excluded category and files of
        a shared repository all stay out."""
        assert world.sync("wiki-db", asset=_ASSET).success

        assert [key for key in world.files("wiki-db") if key.startswith("File/")] == [
            "File/Handbook 2026.pdf",
            "File/Rollout.pptx",
        ]
        assert sorted(files.downloads) == ["Handbook 2026.pdf", "Rollout.pptx"]

    def test_a_file_carries_its_title_and_the_page_citations_link_to(self, world: World, files: FakeMediaWiki):
        world.sync("wiki-db", asset=_ASSET)

        stored = world.s3.objects[("wiki-db", "File/Handbook 2026.pdf")]
        assert stored["Body"] == b"%PDF-1.7 handbook"
        assert {key: unquote(value) for key, value in stored["Metadata"].items()} == {
            "document_title": "Handbook 2026.pdf",
            "source_origin": f"{SITE}/index.php/File:Handbook_2026.pdf",
        }

    def test_an_unchanged_file_is_not_downloaded_again(self, world: World, files: FakeMediaWiki):
        world.sync("wiki-db", asset=_ASSET)
        downloads, writes = len(files.downloads), world.file_writes()

        assert world.sync("wiki-db", asset=_ASSET).success

        assert len(files.downloads) == downloads
        assert world.file_writes() == writes

    def test_a_new_upload_of_a_file_is_downloaded_and_rewritten(self, world: World, files: FakeMediaWiki):
        world.sync("wiki-db", asset=_ASSET)
        files.file("Handbook 2026.pdf")["content"] = b"%PDF-1.7 handbook v2"

        assert world.sync("wiki-db", asset=_ASSET).success

        assert world.s3.objects[("wiki-db", "File/Handbook 2026.pdf")]["Body"] == b"%PDF-1.7 handbook v2"
        assert files.downloads.count("Handbook 2026.pdf") == 2

    def test_a_file_no_synced_page_uses_any_more_is_removed(self, world: World, files: FakeMediaWiki):
        world.sync("wiki-db", asset=_ASSET)
        files.file("Rollout.pptx")["used_by"] = [4]

        assert world.sync("wiki-db", asset=_ASSET).success

        assert "File/Rollout.pptx" not in world.files("wiki-db")
        assert world.announced(world.removed_events) == ["File/Rollout.pptx"]

    def test_a_file_above_the_size_limit_is_left_out(self, world: World, files: FakeMediaWiki):
        files.file("Rollout.pptx")["content"] = b"x" * 1_000_001
        _configure(world, sync_documents=True, max_file_size_mb=1)

        assert world.sync("wiki-db", asset=_ASSET).success

        assert "File/Rollout.pptx" not in world.files("wiki-db")
        assert "Rollout.pptx" not in files.downloads

    def test_a_file_the_wiki_refuses_is_retried_each_run_without_re_reading_the_wiki(
        self, world: World, files: FakeMediaWiki
    ):
        """Counted as missing, it would discard the state after two runs, and every page would be parsed again."""
        files.file("Rollout.pptx")["served_with"] = 403
        world.sync("wiki-db", asset=_ASSET)
        parses = len(files.parses())

        results = [world.sync("wiki-db", asset=_ASSET) for _ in range(2)]

        assert all(result.success for result in results)
        assert files.downloads.count("Rollout.pptx") == 3
        assert files.parses()[parses:] == []
        assert world.step_metadata(results[-1], "reconcile_structured_bucket")["State discarded"] is False
        assert "File/Rollout.pptx" not in world.files("wiki-db")

    def test_an_expired_session_fails_the_sync_instead_of_storing_the_login_page(
        self, world: World, files: FakeMediaWiki, monkeypatch: pytest.MonkeyPatch
    ):
        original = files._download
        monkeypatch.setattr(files, "_download", lambda name: (200, "<html>Sign in</html>", {}))

        result = world.sync("wiki-db", asset=_ASSET)

        monkeypatch.setattr(files, "_download", original)
        assert not result.success
        assert not [key for key in world.files("wiki-db") if key.startswith("File/")]

    def test_the_files_of_a_private_wiki_read_through_oauth_are_synced(self, world: World, files: FakeMediaWiki):
        """The token signs in every download from the wiki, as it does every API request."""
        _configure(
            world, auth_method="oauth", username="", password="", access_token="oauth-secret", sync_documents=True
        )

        assert world.sync("wiki-db", asset=_ASSET).success

        assert {"File/Handbook 2026.pdf", "File/Rollout.pptx"} <= set(world.files("wiki-db"))

    def test_a_file_whose_path_is_taken_is_left_out_and_the_owner_kept(self, world: World, wiki: FakeMediaWiki):
        """The page File:Notes and the file Notes.md are both File/Notes.md; Logo.PNG and Logo.png are both
        File/Logo.png. The page, and the file first by name, keep the path, so nothing flips from run to run."""
        wiki.add_page(60, "Notes", namespace=6, html="<p>The page</p>")
        wiki.add_file(301, "Notes.md", b"# The file", used_by=[1])
        wiki.add_file(302, "Logo.PNG", b"PNG upper", used_by=[1])
        wiki.add_file(303, "Logo.png", b"PNG lower", used_by=[1])
        _configure(world, namespaces=["Main", "Process", "File"], sync_documents=True, sync_images=True)

        assert world.sync("wiki-db", asset=_ASSET).success

        assert "The page" in world.body("wiki-db", "File/Notes.md")
        assert world.s3.objects[("wiki-db", "File/Logo.png")]["Body"] == b"PNG upper"
        assert "Notes.md" not in wiki.downloads and "Logo.png" not in wiki.downloads

    def test_files_of_a_german_wiki_land_in_the_file_collection_too(self, world: World, wiki: FakeMediaWiki):
        """The collection is the namespace's canonical name; Datei is only what that wiki calls it."""
        wiki.local_names = {6: "Datei"}
        wiki.add_file(101, "Handbuch.pdf", b"%PDF-1.7 Handbuch", used_by=[1])
        _configure(world, sync_documents=True)

        assert world.sync("wiki-db", asset=_ASSET).success

        assert "File/Handbuch.pdf" in world.files("wiki-db")
        assert (
            unquote(world.s3.objects[("wiki-db", "File/Handbuch.pdf")]["Metadata"]["document_title"]) == "Handbuch.pdf"
        )


class TestImageSync:
    @pytest.fixture
    def images(self, world: World, wiki: FakeMediaWiki) -> FakeMediaWiki:
        """A wiki whose pages show photos, a template's icon, a photo passed to a template, and a hand-placed icon."""
        wiki.add_page(500, "Infobox", namespace=10)
        wiki.add_file(201, "Team photo.jpg", b"JPEG team", used_by=[1])
        wiki.add_file(202, "Info icon.png", b"PNG icon", used_by=[1, 10, 500], pixels=(400, 400))
        wiki.add_file(203, "Office.png", b"PNG office", used_by=[10])
        wiki.add_file(204, "Bullet.gif", b"GIF bullet", used_by=[2], pixels=(12, 12))
        wiki.add_file(205, "Banner.png", b"PNG banner", used_by=[2], pixels=(1200, 60))
        wiki.add_file(206, "Diagram.svg", b"<svg/>", used_by=[1])
        wiki.add_file(207, "Scan.tif", b"TIFF scan", used_by=[1])
        wiki.add_file(101, "Handbook 2026.pdf", b"%PDF-1.7 handbook", used_by=[1])
        _configure(world, sync_images=True)
        return wiki

    def test_images_are_not_synced_unless_switched_on(self, world: World, images: FakeMediaWiki):
        _configure(world, sync_documents=True)

        assert world.sync("wiki-db", asset=_ASSET).success

        assert [key for key in world.files("wiki-db") if key.startswith("File/")] == ["File/Handbook 2026.pdf"]

    def test_only_content_images_land_in_the_file_collection(self, world: World, images: FakeMediaWiki):
        """A template's own image, images below the minimum size on either side, SVG and tif stay out, and so do the
        documents, which have a switch of their own."""
        assert world.sync("wiki-db", asset=_ASSET).success

        assert [key for key in world.files("wiki-db") if key.startswith("File/")] == [
            "File/Office.png",
            "File/Team photo.jpg",
        ]
        assert sorted(images.downloads) == ["Office.png", "Team photo.jpg"]

    def test_a_minimum_size_of_zero_keeps_small_images(self, world: World, images: FakeMediaWiki):
        _configure(world, sync_images=True, min_image_pixels=0)

        assert world.sync("wiki-db", asset=_ASSET).success

        assert {"File/Bullet.gif", "File/Banner.png"} <= set(world.files("wiki-db"))
        assert "File/Info icon.png" not in world.files("wiki-db")

    def test_documents_and_images_sync_together(self, world: World, images: FakeMediaWiki):
        _configure(world, sync_documents=True, sync_images=True)

        assert world.sync("wiki-db", asset=_ASSET).success

        assert {"File/Handbook 2026.pdf", "File/Office.png", "File/Team photo.jpg"} <= set(world.files("wiki-db"))

    def test_images_switched_off_again_are_removed(self, world: World, images: FakeMediaWiki):
        world.sync("wiki-db", asset=_ASSET)
        _configure(world)

        assert world.sync("wiki-db", asset=_ASSET).success

        assert not [key for key in world.files("wiki-db") if key.startswith("File/")]
