from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

# MUST be the first ``swiss_ai_hub`` import — sets AIHUB_MONGO_MAIN_DB_NAME=aihub_test
# at import time so subsequent ``AIHubSettings()`` instantiations resolve to the test DB.
from swiss_ai_hub.core.testing.db_isolation import _isolate_test_db  # noqa: E402, F401
