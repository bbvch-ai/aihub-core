from unittest.mock import MagicMock, patch

from swiss_ai_hub.pipeline.util.bucket_utils import get_live_namespace_for_directory

BUCKET_UTILS_MODULE = "swiss_ai_hub.pipeline.util.bucket_utils"

CONTAINER = "defaultknowledge"
DIRECTORY = "reports"


def _resolve(*, deleting: bool) -> str | None:
    namespace = MagicMock()
    namespace.namespace_name = DIRECTORY
    namespace.deleting = deleting

    with (
        patch(f"{BUCKET_UTILS_MODULE}.ensure_main_db_connection"),
        patch(f"{BUCKET_UTILS_MODULE}._get_or_create_bucket", return_value=MagicMock()),
        patch(f"{BUCKET_UTILS_MODULE}._get_or_create_namespace", return_value=namespace),
    ):
        return get_live_namespace_for_directory(CONTAINER, DIRECTORY)


class TestGetLiveNamespaceForDirectory:
    def test_returns_the_namespace_of_a_live_directory(self) -> None:
        assert _resolve(deleting=False) == DIRECTORY

    def test_returns_none_while_the_namespace_is_flagged_for_teardown(self) -> None:
        """The caller drops the directory from the observation, so ingestion stops the moment the flag is set
        rather than racing the teardown job that is about to delete the folder."""
        assert _resolve(deleting=True) is None

    def test_still_registers_a_newly_discovered_directory(self) -> None:
        """The lookup creates the NamespaceEntity the knowledge UI reads; a new folder is never already
        flagged, so liveness checking must not stop that side effect."""
        namespace = MagicMock()
        namespace.namespace_name = DIRECTORY
        namespace.deleting = False

        with (
            patch(f"{BUCKET_UTILS_MODULE}.ensure_main_db_connection"),
            patch(f"{BUCKET_UTILS_MODULE}._get_or_create_bucket", return_value=MagicMock()),
            patch(f"{BUCKET_UTILS_MODULE}._get_or_create_namespace", return_value=namespace) as get_or_create,
        ):
            get_live_namespace_for_directory(CONTAINER, DIRECTORY)

        get_or_create.assert_called_once()
