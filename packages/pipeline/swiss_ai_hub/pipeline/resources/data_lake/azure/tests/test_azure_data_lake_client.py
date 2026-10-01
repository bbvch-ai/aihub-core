"""The Azure client shares the listing contract of the S3 one: a namespace collision skips a folder (#1927)."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from swiss_ai_hub.pipeline.resources.data_lake.azure.azure_data_lake_client import AzureDataLakeClient
from swiss_ai_hub.pipeline.util.namespace_collision_error import NamespaceCollisionError

NAMESPACE_PATCH_TARGET = (
    "swiss_ai_hub.pipeline.resources.data_lake.azure.azure_data_lake_client.get_or_create_namespace_for_directory"
)


def _path(name: str, is_directory: bool = False) -> MagicMock:
    path = MagicMock(is_directory=is_directory)
    path.name = name
    return path


def _filesystem(paths: list[MagicMock]) -> MagicMock:
    filesystem = MagicMock()
    filesystem.get_paths.return_value = paths
    properties = MagicMock(size=1, owner="owner", metadata={})
    properties.content_settings.content_md5 = bytes(16)
    properties.content_settings.content_type = "text/markdown"
    timestamps = {
        "last_modified": datetime(2026, 9, 25, tzinfo=UTC),
        "creation_time": datetime(2026, 9, 24, tzinfo=UTC),
    }
    properties.__getitem__.side_effect = timestamps.__getitem__
    properties.__contains__.side_effect = timestamps.__contains__
    filesystem.get_file_client.return_value.get_file_properties.return_value = properties
    return filesystem


def _collide_on_hr_docs(container_name: str, directory_name: str) -> str:
    if directory_name == "hr docs":
        raise NamespaceCollisionError(directory=directory_name, existing_folder="hr_docs", namespace_name="hr_docs")
    return directory_name


PATHS = [
    _path("hr docs", is_directory=True),
    _path("root.md"),
    _path("hr docs/a.md"),
    _path("hr docs/c.md"),
    _path("hr_docs/b.md"),
]


@patch(NAMESPACE_PATCH_TARGET, side_effect=_collide_on_hr_docs)
def test_a_colliding_folder_is_skipped_once_per_directory(namespace: MagicMock) -> None:
    client = AzureDataLakeClient("container", _filesystem(PATHS))

    listing = client.list_files()

    assert [file.uri for file in listing.files] == ["container/hr_docs/b.md"]
    assert [file.uri for file in listing.skipped] == ["container/hr docs/a.md", "container/hr docs/c.md"]
    assert [call.args[1] for call in namespace.call_args_list] == ["hr docs", "hr_docs"]


@patch(NAMESPACE_PATCH_TARGET)
def test_ingestible_uris_need_no_namespace_lookup(namespace: MagicMock) -> None:
    client = AzureDataLakeClient("container", _filesystem(PATHS))

    assert client.list_ingestible_uris() == [
        "container/hr docs/a.md",
        "container/hr docs/c.md",
        "container/hr_docs/b.md",
    ]
    namespace.assert_not_called()
