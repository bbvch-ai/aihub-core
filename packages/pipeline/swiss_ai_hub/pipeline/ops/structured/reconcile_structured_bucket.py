from typing import Annotated

from dagster import OpDefinition, OpExecutionContext, Output, op

from swiss_ai_hub.pipeline.resources.structured.structured_source_state_store import StructuredSourceStateStore
from swiss_ai_hub.pipeline.types.structured_listing import StructuredListing
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_run_tag
from swiss_ai_hub.pipeline.util.store_builders import build_s3_data_lake_client


def reconcile_structured_bucket_op(
    source: Annotated[str, "Source pipeline id this code location runs as"],
) -> OpDefinition:
    """The step that compares the source's listing with the database's files and decides what to remove.

    A file the source no longer lists is removed, except one this run wrote. A listed record without a file means
    the cursor is ahead of the data, after a source switch, a lost file or a layout change, which the cursor alone
    would never repair: the stored state is then discarded, so the next run reads everything again.
    """

    @op(name=f"{source}_reconcile_structured_bucket", code_version="v1")
    def reconcile_structured_bucket(context: OpExecutionContext, listing: StructuredListing) -> Output[list[str]]:
        bucket = bucket_from_run_tag(context)
        client = build_s3_data_lake_client(bucket, ensure_bucket=False)
        present = set(client.list_ingestible_uris())
        listed = {client.build_uri(key) for key in listing.listed_keys}
        written = {client.build_uri(key) for key in listing.written_keys}
        if not listed and present:
            raise ValueError(
                f"The source listed no records while '{bucket}' holds {len(present)} files; refusing to empty the "
                "database. Check the source's credentials and scope."
            )
        missing = listed - present
        if missing:
            StructuredSourceStateStore(source, bucket).delete()
            context.log.warning(
                f"{len(missing)} listed record(s) of '{bucket}' have no file; the next run re-reads the whole source."
            )
        to_remove = sorted(present - listed - written)
        return Output(
            to_remove,
            metadata={
                "Files to remove": len(to_remove),
                "Listed records without a file": len(missing),
                "Written but not listed": len(written - listed),
            },
        )

    return reconcile_structured_bucket
