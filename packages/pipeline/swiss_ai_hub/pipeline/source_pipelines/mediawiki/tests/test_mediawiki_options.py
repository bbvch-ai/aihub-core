import pytest
from pydantic import ValidationError
from swiss_ai_hub.core.infrastructure import MineruSettings

from swiss_ai_hub.pipeline.source_pipelines.mediawiki.mediawiki_options import MediaWikiOptions
from swiss_ai_hub.pipeline.source_pipelines.structured_sync_config import StructuredSyncConfig


def _options(**changes: object) -> MediaWikiOptions:
    return MediaWikiOptions.model_validate(
        {"base_url": "https://wiki.acme.ch", "username": "Sync bot@pipeline", "password": "bot-secret", **changes}
    )


class TestValues:
    def test_categories_are_stored_without_prefix_or_underscores_sorted_and_once(self):
        options = _options(exclude_categories=["Category:Hide_From_AI", " Hide From AI ", "category:Drafts", ""])

        assert options.excluded_categories() == ["Drafts", "Hide From AI"]

    def test_category_case_is_kept_for_wikis_with_case_sensitive_titles(self):
        assert _options(include_categories=["drafts"]).included_categories() == ["drafts"]

    def test_namespaces_default_to_the_main_namespace(self):
        assert _options().namespace_names() == ["0"]
        assert _options(namespaces="").namespace_names() == ["0"]

    def test_namespaces_are_sorted_so_reordering_keeps_the_scope(self):
        assert _options(namespaces=["Process", "Main"]).namespace_names() == ["Main", "Process"]

    @pytest.mark.parametrize("url", ["https://wiki.acme.ch/?title=x", "https://user:pw@wiki.acme.ch", "ftp://wiki"])
    def test_a_url_that_could_name_another_address_is_refused_when_saved(self, url: str):
        with pytest.raises(ValidationError):
            _options(base_url=url)

    def test_an_unknown_sign_in_method_is_refused_when_saved(self):
        with pytest.raises(ValidationError):
            _options(auth_method="kerberos")


class TestProblems:
    def test_a_complete_configuration_has_none(self):
        assert _options().problems() == []

    def test_oauth_needs_a_token_but_no_user_name_or_password(self):
        oauth = {"auth_method": "oauth", "username": "", "password": ""}

        assert _options(**oauth).problems() == ["the OAuth access token is missing"]
        assert _options(**oauth, access_token="oauth-secret").problems() == []


class TestOAuthToken:
    def test_the_token_is_sent_only_while_oauth_is_the_sign_in(self):
        """A token left over from an earlier setting must not travel along with a password sign-in."""
        assert _options(auth_method="oauth", access_token="oauth-secret").oauth_token() == "oauth-secret"
        assert _options(auth_method="bot_password", access_token="oauth-secret").oauth_token() is None

    def test_a_sign_in_without_credentials_names_what_is_missing(self):
        assert _options(base_url="", username="", password="").problems() == [
            "the wiki URL is missing",
            "the user name is missing",
            "the password is missing",
        ]

    def test_an_anonymous_reader_needs_no_credentials(self):
        assert _options(auth_method="anonymous", username="", password="").problems() == []


class TestStructuredSyncConfig:
    @pytest.mark.parametrize("path", ["mediawiki.password", "mediawiki.access_token"])
    def test_the_credentials_are_secrets_the_api_encrypts(self, path: str):
        assert path in StructuredSyncConfig.as_form().secret_field_paths()

    def test_a_rotated_password_keeps_the_scope_fingerprint(self):
        """A new password must keep the sync state; a new category must not."""

        def fingerprint(**changes: object) -> str:
            options = {"base_url": "https://wiki.acme.ch", "username": "bot", "password": "one", **changes}
            return StructuredSyncConfig.model_validate(
                {"source_kind": "mediawiki", "mediawiki": options}
            ).scope_fingerprint()

        assert fingerprint(password="two") == fingerprint()
        assert fingerprint(exclude_categories=["Drafts"]) != fingerprint()

    def test_mediawiki_is_offered_as_a_kind(self):
        options = StructuredSyncConfig.as_form().source_kind.options

        assert "mediawiki" in [option["value"] for option in options]


class TestFileOptions:
    def test_files_are_not_synced_unless_switched_on(self):
        assert _options().sync_documents is False

    def test_the_size_limit_is_in_megabytes(self):
        assert _options(max_file_size_mb=2).max_file_bytes() == 2_000_000

    @pytest.mark.parametrize("size", [0, 501])
    def test_a_size_limit_out_of_range_is_refused_when_saved(self, size: int):
        with pytest.raises(ValidationError):
            _options(max_file_size_mb=size)

    def test_nothing_is_synced_but_pages_by_default(self):
        options = _options()

        assert not options.syncs_files()
        assert options.file_types() == frozenset()
        assert options.min_image_pixels == 100

    def test_documents_leave_out_images_and_old_office_formats(self):
        types = _options(sync_documents=True).file_types()

        assert {"pdf", "docx", "pptx", "xlsx"} <= types
        assert not {"png", "jpg", "doc", "ppt", "zip"} & types

    def test_images_alone_are_files_to_sync(self):
        options = _options(sync_images=True)

        assert options.syncs_files()
        assert {"png", "jpg", "jpeg", "gif", "tiff"} <= options.file_types()
        assert not {"pdf", "svg", "tif"} & options.file_types()

    def test_images_are_the_types_the_parser_reads(self):
        """A type MinerU does not know would fail the ingestion of every such image."""
        assert MediaWikiOptions.image_types() <= set(MineruSettings().EXTENSIONS)

    @pytest.mark.parametrize("pixels", [-1, 2001])
    def test_a_minimum_image_size_out_of_range_is_refused_when_saved(self, pixels: int):
        with pytest.raises(ValidationError):
            _options(min_image_pixels=pixels)
