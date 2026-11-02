from dagster import Config, MetadataValue, OpExecutionContext, Output, TableColumn, TableRecord, TableSchema, op

from swiss_ai_hub.pipeline.services.orphaned_node_repair_service import OrphanedNodeRepairService
from swiss_ai_hub.pipeline.types.orphaned_node_repair_report import OrphanedNodeRepairReport
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_run_tag


class RepairOrphanedNodesConfig(Config):
    """A dry run by default, so a launch without run config only reports what a real run would delete."""

    dry_run: bool = True


@op(description="Finds and deletes vector nodes whose document has no record and no file in the data lake.")
def repair_orphaned_nodes_op(
    context: OpExecutionContext, config: RepairOrphanedNodesConfig
) -> Output[OrphanedNodeRepairReport]:
    """Adapter around ``OrphanedNodeRepairService``; the target database comes from the ``aihub/bucket`` tag."""
    report = OrphanedNodeRepairService.repair(bucket=bucket_from_run_tag(context), dry_run=config.dry_run)
    context.log.info(
        f"{report.orphaned_nodes} orphaned nodes of {report.orphaned_documents} documents, "
        f"{report.deleted_nodes} deleted (dry run: {report.dry_run})"
    )
    return Output(
        report,
        metadata={
            "dry_run": report.dry_run,
            "orphaned_documents": report.orphaned_documents,
            "orphaned_nodes": report.orphaned_nodes,
            "deleted_nodes": report.deleted_nodes,
            "nodes_by_document": MetadataValue.table(
                records=[
                    TableRecord({"document_id": document_id, "nodes": nodes})
                    for document_id, nodes in sorted(report.nodes_by_document.items())
                ],
                schema=TableSchema(
                    columns=[TableColumn("document_id", "string"), TableColumn("nodes", "int")],
                ),
            ),
        },
    )
