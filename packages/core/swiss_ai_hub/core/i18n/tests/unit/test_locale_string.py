from swiss_ai_hub.core.i18n.locale_string import LocaleString


def test_in_locale_returns_requested_locale():
    locale_string = LocaleString(de="Hallo", en="Hello", fr="Bonjour", it="Ciao")
    assert locale_string.in_locale("en") == "Hello"


def test_in_locale_falls_back_to_default_locale_when_requested_is_unset():
    locale_string = LocaleString(de="Hallo", fr="Bonjour")
    assert locale_string.in_locale("en") == "Hallo"


def test_in_locale_falls_back_to_first_available_when_default_is_unset():
    locale_string = LocaleString(it="Ciao")
    assert locale_string.in_locale("en") == "Ciao"


def test_in_locale_unknown_locale_falls_back_instead_of_returning_none():
    locale_string = LocaleString(de="Hallo", en="Hello")
    assert locale_string.in_locale("es") == "Hallo"


def test_in_locale_skips_empty_default_locale_and_returns_first_available():
    locale_string = LocaleString(fr="Bonjour")
    assert locale_string.in_locale("de") == "Bonjour"


def test_in_locale_returns_none_when_every_locale_is_empty():
    assert LocaleString().in_locale("en") is None


def test_in_locale_strict_returns_requested_locale():
    locale_string = LocaleString(de="Hallo", en="Hello")
    assert locale_string.in_locale("en", fallback=False) == "Hello"


def test_in_locale_strict_returns_none_without_falling_back():
    locale_string = LocaleString(de="Hallo")
    assert locale_string.in_locale("en", fallback=False) is None
    assert locale_string.in_locale("es", fallback=False) is None
