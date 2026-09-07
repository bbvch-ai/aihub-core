from unittest.mock import MagicMock, patch

from dagster import DagsterInstance, build_op_context

from swiss_ai_hub.pipeline.ops.teardown.knowledge_teardown_op import KnowledgeTeardownConfig, knowledge_teardown_op

OP_MODULE = "swiss_ai_hub.pipeline.ops.teardown.knowledge_teardown_op"

CONFIG = KnowledgeTeardownConfig(
    namespace_id="6501f0000000000000000001",
    namespace_name="reports",
    folder_name="reports",
    db_name="defaultknowledge",
)


class TestKnowledgeTeardownOp:
    def test_delegates_to_the_service_with_the_run_config(self) -> None:
        data_lake_client = MagicMock()
        service = MagicMock()

        with (
            patch(f"{OP_MODULE}.ensure_main_db_connection"),
            patch(f"{OP_MODULE}.KnowledgeTeardownService", service),
        ):
            knowledge_teardown_op(
                build_op_context(
                    instance=DagsterInstance.ephemeral(),
                    op_config=CONFIG.model_dump(),
                    resources={"data_lake_client": data_lake_client},
                )
            )

        service.teardown_namespace.assert_called_once_with(
            namespace_id=CONFIG.namespace_id,
            namespace_name=CONFIG.namespace_name,
            folder_name=CONFIG.folder_name,
            db_name=CONFIG.db_name,
            data_lake_client=data_lake_client,
        )

    def test_leaves_the_dynamic_partition_registry_alone(self) -> None:
        """Namespace teardown needs no partition purge: the next observation no longer enumerates the folder,
        so ``replace_partition_keys`` reconciles its keys away by itself."""
        instance = DagsterInstance.ephemeral()
        registry = "defaultknowledge_document_partitions"
        instance.add_dynamic_partitions(registry, ["s3://defaultknowledge/reports/a.pdf"])

        with (
            patch(f"{OP_MODULE}.ensure_main_db_connection"),
            patch(f"{OP_MODULE}.KnowledgeTeardownService"),
        ):
            knowledge_teardown_op(
                build_op_context(
                    instance=instance,
                    op_config=CONFIG.model_dump(),
                    resources={"data_lake_client": MagicMock()},
                )
            )

        assert instance.get_dynamic_partitions(registry) == ["s3://defaultknowledge/reports/a.pdf"]
