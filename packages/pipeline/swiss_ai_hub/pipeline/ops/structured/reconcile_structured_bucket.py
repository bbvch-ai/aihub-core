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

    A file the source no longer lists is removed, except one this run wrote. A record listed without a file in two
    runs in a row means the cursor is ahead of the data, after a source switch, a lost file or a sync slower than the
    cursor's overlap, which the cursor alone would never repair: the stored state is then discarded, so the next run
    reads everything again. Missing once is not enough, because a record created while a run is between its sync and
    its listing is missing too, and the next run fetches it anyway. A file the source would not serve this run is not
    missing in that sense: the sync forgot it, so the next run tries it again without the whole source being re-read.
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
        unread = set(listing.unread_file_keys)
        missing = {key for key in listing.listed_keys if client.build_uri(key) not in present and key not in unread}
        missing_again = _settle_missing(context, StructuredSourceStateStore(source, bucket), bucket, missing)
        to_remove = sorted(present - listed - written)
        return Output(
            to_remove,
            metadata={
                "Files to remove": len(to_remove),
                "Listed records without a file": len(missing),
                "Missing in two runs in a row": len(missing_again),
                "State discarded": bool(missing_again),
                "Written but not listed": len(written - listed),
                "Files not served by the source": len(unread),
            },
        )

    return reconcile_structured_bucket


def _settle_missing(
    context: OpExecutionContext, store: StructuredSourceStateStore, bucket: str, missing: set[str]
) -> set[str]:
    """Discards the state when a record was already missing at the last run, else remembers this run's missing
    records for the next one. Returns the records missing in both runs."""
    missing_again = missing & store.missing_at_last_run()
    if missing_again:
        store.delete()
        context.log.warning(
            f"{len(missing_again)} listed record(s) of '{bucket}' were missing in two runs in a row; the next run "
            "re-reads the whole source."
        )
        return missing_again
    store.remember_missing(missing)
    if missing:
        context.log.info(
            f"{len(missing)} listed record(s) of '{bucket}' have no file; if they are still missing at the next run, "
            "that run discards the state."
        )
    return missing_again
