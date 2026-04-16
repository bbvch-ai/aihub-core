from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

from swiss_ai_hub.core.testing.auth_utils.user_mocks import mock_keycloak_admin_service_autouse  # noqa: E402, F401

# Must be imported before anything that constructs ``AIHubSettings`` — the module
# sets ``AIHUB_MONGO_MAIN_DB_NAME=aihub_test`` at import time so the test DB is used.
from swiss_ai_hub.core.testing.db_isolation import _isolate_test_db  # noqa: E402, F401
