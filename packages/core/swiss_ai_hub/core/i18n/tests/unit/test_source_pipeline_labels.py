import pytest

from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.persistence.rag.datalake.entities.source_pipeline_type import SourcePipelineType

_LOCALES = ("en", "de", "fr", "it")


def _assert_translated(path: str) -> None:
    """A missing key resolves to the path itself, so an untranslated label would reach the UI as raw text."""
    label = LocaleString.from_i18n_path(path)
    for locale in _LOCALES:
        value = getattr(label, locale)
        assert value, f"{path} is empty in {locale}"
        assert value != path, f"{path} is missing in {locale}"


@pytest.mark.parametrize("source", [source_type.value for source_type in SourcePipelineType])
@pytest.mark.parametrize("field", ["display_name", "description"])
def test_every_shipped_source_pipeline_is_labelled_in_every_language(source: str, field: str):
    _assert_translated(f"lib.source_pipelines.{source}.{field}")


@pytest.mark.parametrize("field", ["label", "help"])
def test_the_structured_source_kind_selector_is_labelled_in_every_language(field: str):
    _assert_translated(f"lib.source_pipelines.structured.config.source_kind.{field}")


@pytest.mark.parametrize(
    "path",
    [
        "display_name",
        *(
            f"{field}.{part}"
            for field in ("base_url", "deployment", "email", "api_token", "project_keys", "jql")
            for part in ("label", "help")
        ),
        "deployment.cloud",
        "deployment.data_center",
    ],
)
def test_the_jira_form_is_labelled_in_every_language(path: str):
    _assert_translated(f"lib.source_pipelines.structured.config.jira.{path}")


@pytest.mark.parametrize(
    "path",
    [
        "display_name",
        *(
            f"{field}.{part}"
            for field in ("base_url", "deployment", "email", "api_token", "space_keys", "labels", "ancestor_page_ids")
            for part in ("label", "help")
        ),
        "deployment.cloud",
        "deployment.data_center",
    ],
)
def test_the_confluence_form_is_labelled_in_every_language(path: str):
    _assert_translated(f"lib.source_pipelines.structured.config.confluence.{path}")


@pytest.mark.parametrize(
    "path",
    [
        "display_name",
        *(
            f"{field}.{part}"
            for field in (
                "base_url",
                "auth_method",
                "username",
                "password",
                "access_token",
                "namespaces",
                "include_categories",
                "exclude_categories",
                "sync_files",
                "max_file_size_mb",
            )
            for part in ("label", "help")
        ),
        "auth_method.bot_password",
        "auth_method.web_form",
        "auth_method.oauth",
        "auth_method.anonymous",
    ],
)
def test_the_mediawiki_form_is_labelled_in_every_language(path: str):
    _assert_translated(f"lib.source_pipelines.structured.config.mediawiki.{path}")
