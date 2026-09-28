from unittest.mock import MagicMock, patch

from dagster import build_op_context

from swiss_ai_hub.pipeline.ops.source.routed.announce_removed_files import announce_removed_files
from swiss_ai_hub.pipeline.ops.source.routed.build_data_lake_uri_for_bucket import build_data_lake_uri_for_bucket
from swiss_ai_hub.pipeline.ops.source.routed.fetch_bucket_files_to_remove import fetch_bucket_files_to_remove
from swiss_ai_hub.pipeline.ops.source.routed.write_data_lake_file_to_bucket import write_data_lake_file_to_bucket
from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
from swiss_ai_hub.pipeline.types.rclone_file import MinimalRcloneFile, RcloneFile
from swiss_ai_hub.pipeline.util.run_routing import BUCKET_RUN_TAG

_ROUTED = "swiss_ai_hub.pipeline.ops.source.routed"


def _source_file(path: str) -> RcloneFile:
    return RcloneFile(
        name=path.rsplit("/", 1)[-1],
        path=path,
        content=b"x",
        size=1,
        modified=1,
        created=1,
        remote="r:",
        remote_path=path,
    )


class TestBuildDataLakeUriForBucket:
    def test_the_uri_is_the_bucket_of_the_partition_plus_the_remote_path_with_no_prefix(self):
        context = build_op_context(partition_key="hrdocs|Policies%2Fhandbook.pdf")

        assert (
            build_data_lake_uri_for_bucket(context, _source_file("/Policies/handbook.pdf"))
            == "s3://hrdocs/Policies/handbook.pdf"
        )


class TestWriteDataLakeFileToBucket:
    def test_writes_then_announces_and_returns_the_file_without_content(self):
        context = build_op_context(partition_key="hrdocs|Policies%2Fhandbook.pdf")
        client = MagicMock()
        with (
            patch(f"{_ROUTED}.write_data_lake_file_to_bucket.build_s3_data_lake_client", return_value=client),
            patch(f"{_ROUTED}.write_data_lake_file_to_bucket.notify_source_updated") as notify,
        ):
            output = write_data_lake_file_to_bucket(
                context, b"pdf-bytes", {"k": "v"}, "s3://hrdocs/Policies/handbook.pdf"
            )

        put = client.raw_client.put_object.call_args.kwargs
        assert (put["Bucket"], put["Key"], put["Body"]) == ("hrdocs", "Policies/handbook.pdf", b"pdf-bytes")
        notify.assert_called_once_with("hrdocs", ["Policies/handbook.pdf"])
        assert output.value.uri == "s3://hrdocs/Policies/handbook.pdf"
        assert output.value.content is None


class TestFetchBucketFilesToRemove:
    def test_everything_the_source_no_longer_lists_is_an_orphan(self):
        context = build_op_context(run_tags={BUCKET_RUN_TAG: "hrdocs"})
        client = MagicMock()
        client.build_uri.side_effect = lambda file_path: f"s3://hrdocs/{file_path}"
        client.get_all_files.return_value = [
            DataLakeFile.from_content(uri="s3://hrdocs/Policies/keep.pdf", content=b"k"),
            DataLakeFile.from_content(uri="s3://hrdocs/Policies/gone.pdf", content=b"g"),
        ]
        with patch(f"{_ROUTED}.fetch_bucket_files_to_remove.build_s3_data_lake_client", return_value=client):
            removed = fetch_bucket_files_to_remove(
                context, [MinimalRcloneFile(name="keep.pdf", path="/Policies/keep.pdf", size=1, modified=1)]
            )

        assert [file.uri for file in removed] == ["s3://hrdocs/Policies/gone.pdf"]


class TestAnnounceRemovedFiles:
    def test_one_object_key_per_removed_file(self):
        context = build_op_context(run_tags={BUCKET_RUN_TAG: "hrdocs"})
        removed = [DataLakeFile.from_content(uri="s3://hrdocs/Policies/gone.pdf", content=b"g")]
        with patch(f"{_ROUTED}.announce_removed_files.notify_source_updated") as notify:
            output = announce_removed_files(context, removed)

        notify.assert_called_once_with("hrdocs", ["Policies/gone.pdf"])
        assert output.value == removed
