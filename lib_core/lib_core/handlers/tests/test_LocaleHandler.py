from typing import Dict, List

import pytest

from lib_core.handlers.LocaleHandler import LocaleHandler
from lib_core.entities.MultiLocale import MultiLocale


def test_all_languages_present(yaml_files: Dict[str, List[str]]):
    missing_languages = {}
    for base_name, files in yaml_files.items():
        languages = set(file.split(".")[-2] for file in files)
        if languages != set(LocaleHandler.LOCALE_WHITE_LIST):
            missing = set(LocaleHandler.LOCALE_WHITE_LIST) - languages
            missing_languages[base_name] = missing

    if missing_languages:
        error_msg = "The following files are missing translations:\n"
        for base_name, missing in missing_languages.items():
            error_msg += f"  {base_name}: missing {', '.join(missing)}\n"
        pytest.fail(error_msg)


def test_extract_with_valid_locale_returns_correct_translation(
    dict_locale_data: dict,
):
    assert LocaleHandler.extract(dict_locale_data, "de") == "Such-Agent"


def test_extract_with_invalid_locale_uses_default_locale(dict_locale_data: dict):
    assert LocaleHandler.extract(dict_locale_data, "es") == "Such-Agent"


def test_extract_with_missing_locale_returns_first_available():
    assert LocaleHandler.extract({"it": "Agente di ricerca"}, "de") == "Agente di ricerca"


def test_extract_from_multi_locale_with_valid_locale_returns_correct_translation(
    multi_locale_data: MultiLocale,
):
    assert LocaleHandler.extract(multi_locale_data, "de") == "Such-Agent"


def test_extract_from_multi_locale_with_invalid_locale_uses_default_locale(
    multi_locale_data: MultiLocale,
):
    assert LocaleHandler.extract(multi_locale_data, "es") == "Such-Agent"


def test_extract_from_multi_locale_with_missing_locale_returns_first_available():
    partial_locale_data = MultiLocale(it="Agente di ricerca")
    assert LocaleHandler.extract(partial_locale_data, "de") == "Agente di ricerca"


def test_t_object_returns_correct_translation(mocker):
    mocker.patch("builtins.open", mocker.mock_open(read_data="name: Such-Agent"))
    result = LocaleHandler.t_object("agent.prompt.name", "de")
    assert result == "Such-Agent"


def test_t_object_with_nonexistent_file_raises_file_not_found_error():
    with pytest.raises(FileNotFoundError):
        LocaleHandler.t_object("nonexistent.folder.name", "de")
