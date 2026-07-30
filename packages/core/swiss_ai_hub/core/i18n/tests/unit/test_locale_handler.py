import os

import pytest

from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString

LANG_FOLDER = os.path.join(os.path.dirname(__file__), "../translations")


def _create_yaml_files(directory: str) -> dict[str, list[str]]:
    yaml_files = {}
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".yml"):
                base_name = file.rsplit(".", 2)[0]
                if base_name not in yaml_files:
                    yaml_files[base_name] = []
                yaml_files[base_name].append(os.path.join(root, file))
    return yaml_files


@pytest.fixture(scope="module")
def yaml_files() -> dict[str, list[str]]:
    return _create_yaml_files(LANG_FOLDER)


@pytest.fixture(scope="module")
def dict_locale_data() -> dict:
    return {
        "en": "Search-Agent",
        "de": "Such-Agent",
        "fr": "Agent de recherche",
        "it": "Agente di ricerca",
    }


@pytest.fixture(scope="module")
def multi_locale_data() -> LocaleString:
    return LocaleString(
        en="Search-Agent",
        de="Such-Agent",
        fr="Agent de recherche",
        it="Agente di ricerca",
    )


def test_all_languages_present(yaml_files: dict[str, list[str]]):
    missing_languages = {}
    for base_name, files in yaml_files.items():
        languages = set(file.split(".")[-2] for file in files)
        if languages != set(LocaleHandler().LOCALE_WHITE_LIST):
            missing = set(LocaleHandler().LOCALE_WHITE_LIST) - languages
            missing_languages[base_name] = missing

    if missing_languages:
        error_msg = "The following files are missing translations:\n"
        for base_name, missing in missing_languages.items():
            error_msg += f"  {base_name}: missing {', '.join(missing)}\n"
        pytest.fail(error_msg)


def test_extract_with_valid_locale_returns_correct_translation(
    dict_locale_data: dict,
):
    assert LocaleHandler().extract(dict_locale_data, "de") == "Such-Agent"


def test_extract_with_invalid_locale_uses_default_locale(dict_locale_data: dict):
    assert LocaleHandler().extract(dict_locale_data, "es") == "Such-Agent"


def test_extract_with_missing_locale_returns_first_available():
    assert LocaleHandler().extract({"it": "Agente di ricerca"}, "de") == "Agente di ricerca"


def test_extract_from_multi_locale_with_valid_locale_returns_correct_translation(
    multi_locale_data: LocaleString,
):
    assert LocaleHandler().extract(multi_locale_data, "de") == "Such-Agent"


def test_extract_from_multi_locale_with_invalid_locale_uses_default_locale(
    multi_locale_data: LocaleString,
):
    assert LocaleHandler().extract(multi_locale_data, "es") == "Such-Agent"


def test_extract_from_multi_locale_with_missing_locale_returns_first_available():
    partial_locale_data = LocaleString(it="Agente di ricerca")
    assert LocaleHandler().extract(partial_locale_data, "de") == "Agente di ricerca"


def test_extract_from_empty_multi_locale_returns_none():
    assert LocaleHandler().extract(LocaleString(), "de") is None


def test_extract_from_all_empty_dict_returns_none():
    assert LocaleHandler().extract({"de": None}, "de") is None


def test_t_object_with_nonexistent_file_raises_file_not_found_error():
    with pytest.raises(FileNotFoundError):
        LocaleHandler().t_object("nonexistent.folder.name", "de")
