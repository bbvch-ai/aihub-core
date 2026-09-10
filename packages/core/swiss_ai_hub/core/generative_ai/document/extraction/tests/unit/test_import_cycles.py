import subprocess
import sys

import pytest

# `core.imap.draft_email_settings` imports `core.generative_ai...llm_config`, and `EmlLoader` now imports
# `core.imap.mail_parser` — an edge in the opposite direction. No cycle forms today because both package
# `__init__.py`s are lazy and the loader reaches for the concrete module rather than the package. All three of
# those properties are easy to undo by accident, and undoing any one breaks `import swiss_ai_hub.core.generative_ai`
# for every consumer, the RAG agent included. Hence a test that actually imports, in a clean interpreter each time.
_ORDERS = [
    "import swiss_ai_hub.core.generative_ai, swiss_ai_hub.core.imap",
    "import swiss_ai_hub.core.imap, swiss_ai_hub.core.generative_ai",
    "from swiss_ai_hub.core.generative_ai import EmlLoader; from swiss_ai_hub.core.imap import MailParser",
    "from swiss_ai_hub.core.imap import DraftEmailSettings; from swiss_ai_hub.core.generative_ai import EmlLoader",
    (
        "from swiss_ai_hub.core.imap.draft_email_settings import DraftEmailSettings; "
        "from swiss_ai_hub.core.generative_ai.document.loaders.eml_loader import EmlLoader"
    ),
    (
        "from swiss_ai_hub.core.generative_ai.document.loaders.eml_loader import EmlLoader; "
        "from swiss_ai_hub.core.imap.draft_email_settings import DraftEmailSettings"
    ),
]


@pytest.mark.parametrize("statement", _ORDERS)
def test_core_imap_and_generative_ai_import_in_either_order(statement: str):
    completed = subprocess.run([sys.executable, "-c", statement], capture_output=True, text=True, timeout=120)
    assert completed.returncode == 0, completed.stderr
