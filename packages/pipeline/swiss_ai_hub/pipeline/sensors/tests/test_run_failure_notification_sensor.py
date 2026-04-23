from unittest.mock import MagicMock, patch

from dagster import AssetKey, DefaultSensorStatus, RunStatusSensorDefinition

from swiss_ai_hub.pipeline.sensors.run_failure_notification_sensor import (
    _format_failure_message,
    run_failure_notification_sensor,
)


class TestRunFailureNotificationSensorFactory:
    def test_returns_sensor_with_default_running_status(self) -> None:
        sensor = run_failure_notification_sensor(
            urls=["slack://a/b/c/#ops"],
            dagster_ui_base_url="http://localhost:3000",
        )
        assert isinstance(sensor, RunStatusSensorDefinition)
        assert sensor.name == "run_failure_notification_sensor"
        assert sensor.default_status is DefaultSensorStatus.RUNNING

    def test_respects_custom_name_and_interval(self) -> None:
        sensor = run_failure_notification_sensor(
            urls=["slack://a/b/c/#ops"],
            name="my_custom_sensor",
            minimum_interval_seconds=120,
        )
        assert sensor.name == "my_custom_sensor"
        assert sensor.minimum_interval_seconds == 120


class TestFormatFailureMessage:
    def _build_context(self, asset_keys: list[str] | None, error_message: str | None) -> MagicMock:
        context = MagicMock()
        context.dagster_run.asset_selection = frozenset(AssetKey([key]) for key in asset_keys) if asset_keys else None
        if error_message is None:
            context.failure_event = None
        else:
            context.failure_event.message = error_message
        return context

    def test_includes_asset_keys_and_error(self) -> None:
        context = self._build_context(["documents", "nodes"], "KeyError: 'missing'")
        message = _format_failure_message(context)
        assert "Assets: documents, nodes" in message
        assert "Error: KeyError: 'missing'" in message

    def test_truncates_asset_keys_with_remainder_count(self) -> None:
        context = self._build_context([f"asset_{i}" for i in range(10)], None)
        message = _format_failure_message(context)
        assert "(+5 more)" in message
        assert message.count(",") == 4  # 5 keys → 4 commas

    def test_truncates_long_error_message(self) -> None:
        long_error = "x" * 1000
        context = self._build_context(None, long_error)
        message = _format_failure_message(context)
        assert len(message) < 600
        assert message.endswith("...")

    def test_empty_when_no_assets_and_no_error(self) -> None:
        context = self._build_context(None, None)
        assert _format_failure_message(context) == ""


class TestDispatchDelegatesToApprise:
    def test_sensor_body_calls_notify_run_status(self) -> None:
        with patch("swiss_ai_hub.pipeline.sensors.run_failure_notification_sensor.AppriseResource") as resource_cls:
            resource_instance = resource_cls.return_value
            resource_instance.notify_run_status.return_value = True

            sensor = run_failure_notification_sensor(
                urls=["slack://a/b/c/#ops"],
                dagster_ui_base_url="http://dagster.local",
            )

            context = MagicMock()
            context.dagster_run.asset_selection = frozenset([AssetKey(["documents"])])
            context.dagster_run.run_id = "run-123"
            context.failure_event.message = "boom"

            sensor_fn = sensor._run_status_sensor_fn  # access underlying callable
            sensor_fn(context)

            resource_instance.notify_run_status.assert_called_once()
            _, kwargs = resource_instance.notify_run_status.call_args
            assert kwargs["status"] == "FAILURE"
            assert kwargs["run"] is context.dagster_run
            assert "Assets: documents" in kwargs["message"]
            assert "Error: boom" in kwargs["message"]
