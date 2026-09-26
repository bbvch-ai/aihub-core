from unittest.mock import patch

import pytest
from dagster import build_op_context

from swiss_ai_hub.pipeline.ops.repair.repair_orphaned_nodes_op import (
    RepairOrphanedNodesConfig,
    repair_orphaned_nodes_op,
)
from swiss_ai_hub.pipeline.types.orphaned_node_repair_report import OrphanedNodeRepairReport
from swiss_ai_hub.pipeline.util.run_routing import BUCKET_RUN_TAG

_MODULE = "swiss_ai_hub.pipeline.ops.repair.repair_orphaned_nodes_op"

BUCKET = "researchdocs"


class TestRepairOrphanedNodesOp:
    def test_is_a_dry_run_unless_told_otherwise(self):
        assert RepairOrphanedNodesConfig().dry_run is True

    def test_repairs_the_tagged_database_and_reports_the_counts(self):
        report = OrphanedNodeRepairReport(dry_run=False, nodes_by_document={"doc1": 2, "doc2": 1}, deleted_nodes=3)
        with patch(f"{_MODULE}.OrphanedNodeRepairService") as service:
            service.repair.return_value = report
            output = repair_orphaned_nodes_op(
                build_op_context(run_tags={BUCKET_RUN_TAG: BUCKET}), RepairOrphanedNodesConfig(dry_run=False)
            )

        service.repair.assert_called_once_with(bucket=BUCKET, dry_run=False)
        assert output.value is report
        assert output.metadata["orphaned_documents"].value == 2
        assert output.metadata["orphaned_nodes"].value == 3
        assert output.metadata["deleted_nodes"].value == 3
        assert len(output.metadata["nodes_by_document"].records) == 2

    def test_an_untagged_run_is_rejected(self):
        with patch(f"{_MODULE}.OrphanedNodeRepairService") as service, pytest.raises(ValueError, match=BUCKET_RUN_TAG):
            repair_orphaned_nodes_op(build_op_context(), RepairOrphanedNodesConfig())

        service.repair.assert_not_called()
