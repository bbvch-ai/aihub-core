import os

import pytest_asyncio

from lib_core.handlers.LocaleHandler import LocaleHandler


SIMILARITY_CUTOFF = 0.5
SUPPORTED_LANGUAGES = LocaleHandler.LOCALE_WHITE_LIST
LANG_FOLDER = os.path.join(os.path.dirname(__file__), "lang")

