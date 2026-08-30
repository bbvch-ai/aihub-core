from swiss_ai_hub.pipeline.sensors.nats.observation_sensor_cursor import ObservationSensorCursor


class TestFromCursor:
    def test_missing_cursor_yields_empty_state(self) -> None:
        cursor = ObservationSensorCursor.from_cursor(None)

        assert cursor.pending_events == 0
        assert cursor.first_pending_at is None
        assert cursor.followup_armed is False
        assert cursor.rearm_count == 0

    def test_empty_cursor_yields_empty_state(self) -> None:
        assert ObservationSensorCursor.from_cursor("") == ObservationSensorCursor()

    def test_state_round_trips(self) -> None:
        original = ObservationSensorCursor(
            pending_events=7,
            first_pending_at=1_700_000_000.0,
            max_sequence=42,
            requested_run_key="bucket_to_db_seq_42_r0",
            followup_armed=True,
            handled_truncation="run-abc",
            rearm_count=3,
        )

        assert ObservationSensorCursor.from_cursor(original.model_dump_json()) == original

    def test_unparseable_cursor_degrades_to_empty_state(self) -> None:
        """A cursor written by an older version of the model must not wedge the sensor into
        permanently failing ticks."""
        assert ObservationSensorCursor.from_cursor("{not valid json") == ObservationSensorCursor()

    def test_cursor_with_unknown_shape_degrades_to_empty_state(self) -> None:
        assert ObservationSensorCursor.from_cursor('{"pending_events": "many"}') == ObservationSensorCursor()
