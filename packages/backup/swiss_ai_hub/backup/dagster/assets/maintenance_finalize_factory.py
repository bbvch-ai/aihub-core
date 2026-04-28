from dagster import AssetExecutionContext, AssetIn, AssetKey, AssetsDefinition, Failure, asset

from swiss_ai_hub.backup.dagster.types import MaintenanceContext
from swiss_ai_hub.backup.maintenance.base import MaintenanceResult


def maintenance_finalize_factory(
    key: AssetKey,
    session_key: AssetKey,
    service_keys: dict[str, AssetKey],
) -> AssetsDefinition:
    @asset(
        key=key,
        group_name="maintenance",
        ins={
            "session": AssetIn(key=session_key),
            **{name: AssetIn(key=ak) for name, ak in service_keys.items()},
        },
        description="Aggregate maintenance handler results and surface them in the UI.",
    )
    def maintenance_finalize(
        context: AssetExecutionContext,
        session: MaintenanceContext,
        **service_results: MaintenanceResult,
    ) -> list[MaintenanceResult]:
        results = list(service_results.values())
        failed = [r for r in results if not r.succeeded]
        total_rows = sum(r.rows_affected or 0 for r in results)
        total_duration = sum(r.duration_seconds for r in results)

        context.log.info(
            "Maintenance run %s: %d/%d succeeded, %d total rows affected, %.1fs total",
            session.run_id,
            len(results) - len(failed),
            len(results),
            total_rows,
            total_duration,
        )

        context.add_output_metadata(
            {
                "total_handlers": len(results),
                "succeeded": len(results) - len(failed),
                "failed": len(failed),
                "total_rows_affected": total_rows,
                "total_duration_seconds": round(total_duration, 1),
            },
        )

        if failed:
            failed_names = ", ".join(r.name for r in failed)
            raise Failure(
                description=f"Maintenance failed for: {failed_names}",
                metadata={"failed_handlers": failed_names},
            )
        return results

    return maintenance_finalize
