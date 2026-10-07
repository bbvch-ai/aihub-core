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
