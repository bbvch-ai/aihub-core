from unittest.mock import MagicMock, patch

from dagster import (
    AssetKey,
    DagsterEventType,
    DagsterInstance,
    DefaultSensorStatus,
    RunStatusSensorDefinition,
    build_run_status_sensor_context,
    job,
    op,
)

from swiss_ai_hub.pipeline.sensors.run_failure_notification_sensor import (
    _format_failure_message,
    run_failure_notification_sensor,
    run_failure_notification_sensors_from_settings,
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


@op
def _failing_op() -> None:
    raise RuntimeError("boom")


@job
def _failing_job() -> None:
    _failing_op()


class TestDispatchDelegatesToApprise:
    def test_sensor_body_calls_notify_run_status(self) -> None:
        with patch("swiss_ai_hub.pipeline.sensors.run_failure_notification_sensor.AppriseResource") as resource_cls:
            resource_instance = resource_cls.return_value
            resource_instance.notify_run_status.return_value = True

            sensor = run_failure_notification_sensor(
                urls=["slack://a/b/c/#ops"],
                dagster_ui_base_url="http://dagster.local",
            )

            with DagsterInstance.ephemeral() as instance:
                result = _failing_job.execute_in_process(instance=instance, raise_on_error=False)
                assert not result.success
                run = instance.get_run_by_id(result.run_id)
                assert run is not None
                failure_entry = next(
                    entry for entry in instance.all_logs(result.run_id, of_type=DagsterEventType.RUN_FAILURE)
                )
                context = build_run_status_sensor_context(
                    sensor_name="run_failure_notification_sensor",
                    dagster_event=failure_entry.dagster_event,
                    dagster_instance=instance,
                    dagster_run=run,
                )
                sensor(context)

            resource_instance.notify_run_status.assert_called_once()
            _, kwargs = resource_instance.notify_run_status.call_args
            assert kwargs["status"] == "FAILURE"
            assert kwargs["run"].run_id == result.run_id
            # Op-based job has no asset_selection → only the error preview is in the body.
            # The RUN_FAILURE event carries a high-level message, not the op-level exception text.
            assert "Error: " in kwargs["message"]
            assert "_failing_job" in kwargs["message"]


class TestFromSettings:
    def test_returns_empty_when_urls_unset(self, monkeypatch) -> None:
        monkeypatch.delenv("NOTIFICATION_URLS", raising=False)
        assert run_failure_notification_sensors_from_settings() == []

    def test_returns_empty_when_urls_empty_string(self, monkeypatch) -> None:
        monkeypatch.setenv("NOTIFICATION_URLS", "")
        assert run_failure_notification_sensors_from_settings() == []

    def test_returns_one_sensor_with_parsed_urls(self, monkeypatch) -> None:
        monkeypatch.setenv("NOTIFICATION_URLS", "slack://a/b/c/#ops, mailto://u:p@smtp.example.com")
        sensors = run_failure_notification_sensors_from_settings()
        assert len(sensors) == 1
        assert sensors[0].name == "run_failure_notification_sensor"
