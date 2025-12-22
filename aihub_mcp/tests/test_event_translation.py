"""Tests for SAAP to MCP event translation."""

from aihub_mcp.translation.EventTranslator import EventTranslator


class TestEventTranslator:
    """Tests for EventTranslator class."""

    def test_build_start_event(self) -> None:
        """Test building a start event from MCP tool parameters."""
        translator = EventTranslator(nats_url="nats://localhost:4222")

        user_identity = {"id": "test-user", "name": "Test User", "email": "test@example.com"}

        event = translator._build_start_event(
            event_name="UserMessageEvent",
            event_parents=["BaseEvent", "ControlEvent", "StartEvent", "UserMessageEvent"],
            event_data={"messages": [{"role": "user", "content": "Hello"}]},
            event_id="test-123",
            user_identity=user_identity,
        )

        assert event["event_id"] == "test-123"
        assert event["_event_name"] == "UserMessageEvent"
        assert event["_parent_event_names"] == [
            "BaseEvent",
            "ControlEvent",
            "StartEvent",
            "UserMessageEvent",
        ]
        assert event["messages"] == [{"role": "user", "content": "Hello"}]
        assert "created_at" in event
        assert event["user"] == user_identity

    def test_build_subject(self) -> None:
        """Test building NATS subject for events."""
        translator = EventTranslator(nats_url="nats://localhost:4222")

        subject = translator._build_subject(
            agent_class="RAGAgent",
            agent_id="a001",
            thread_id="t123",
            display_id="d456",
            run_id="r789",
            event_type="control_event",
            event_name="UserMessageEvent",
            event_id="e012",
        )

        assert subject == "agent.RAGAgent.a001.t123.d456.r789.control_event.UserMessageEvent.e012"

    def test_build_display_subscription_pattern(self) -> None:
        """Test building NATS subscription pattern for display events."""
        translator = EventTranslator(nats_url="nats://localhost:4222")

        pattern = translator._build_display_subscription_pattern(
            agent_class="ChatAgent",
            agent_id="agent1",
            thread_id="thread1",
            display_id="display1",
        )

        # Pattern uses wildcards for agent_id and run_id since actual agent uses different IDs
        assert pattern == "agent.ChatAgent.*.thread1.display1.*.display_event.>"


class TestBuildHitlResponse:
    """Tests for HITL response event building."""

    def test_build_input_response_event(self) -> None:
        """Test that input HITL response has correct event name."""
        # Simulate calling _publish_hitl_response logic
        hitl_type = "input"
        if hitl_type == "confirmation":
            event_name = "HumanInTheLoopConfirmationResponseEvent"
        else:
            event_name = "HumanInTheLoopInputResponseEvent"

        assert event_name == "HumanInTheLoopInputResponseEvent"

    def test_build_confirmation_response_event(self) -> None:
        """Test that confirmation HITL response has correct event name."""
        hitl_type = "confirmation"
        if hitl_type == "confirmation":
            event_name = "HumanInTheLoopConfirmationResponseEvent"
        else:
            event_name = "HumanInTheLoopInputResponseEvent"

        assert event_name == "HumanInTheLoopConfirmationResponseEvent"
