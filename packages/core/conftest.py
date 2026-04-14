from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

from swiss_ai_hub.core.testing.auth_utils.user_mocks import mock_keycloak_admin_service_autouse  # noqa: E402, F401
