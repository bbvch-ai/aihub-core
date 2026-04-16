import json

import pytest

from swiss_ai_hub.core.events.agent.aitl.exception.agent_in_the_loop_exception_event import (
    AgentInTheLoopExceptionEvent,
)
from swiss_ai_hub.core.events.agent.aitl.request.agent_in_the_loop_request_event import (
    AgentInTheLoopRequestEvent,
)
from swiss_ai_hub.core.events.agent.aitl.response.agent_in_the_loop_response_event import (
    AgentInTheLoopResponseEvent,
)
from swiss_ai_hub.core.events.agent.control.exception.exception_event import ExceptionEvent
from swiss_ai_hub.core.events.agent.control.start.start_event import StartEvent
from swiss_ai_hub.core.events.agent.control.stop.stop_event import StopEvent
from swiss_ai_hub.core.events.agent.display.display_event import DisplayEvent
from swiss_ai_hub.core.events.agent.semantic.llm.llm_stop_event import LLMStopEvent
from swiss_ai_hub.core.events.agent.user.user_message_event import UserMessageEvent
from swiss_ai_hub.core.events.base_event import BaseEvent
from swiss_ai_hub.core.infrastructure.logging.logger import enable_logging
from swiss_ai_hub.core.testing.auth_utils.fake_user import fake_user
from swiss_ai_hub.core.topics import PartialAgentTopic
from swiss_ai_hub.core.testing.auth_utils.user_mocks import mock_keycloak_admin_service_autouse  # noqa: F401


enable_logging()


# ====== Test Fixture Classes ======


class TestStartEvent(StartEvent):
    """A simple test start event."""

    message: str


class TestStopEvent(StopEvent):
    """A simple test stop event."""

    result: int


class TestExceptionEvent(ExceptionEvent):
    """A simple test exception event."""

    message: str


class TestDisplayEvent(DisplayEvent):
    """A simple test display event."""

    content: str


# ====== Fixtures ======


@pytest.fixture
def test_start_event():
    return TestStartEvent(message="Hello, world!", agent_id="test-agent-1")


@pytest.fixture
def test_stop_event():
    return TestStopEvent(result=42)


@pytest.fixture
def test_exception_event():
    return TestExceptionEvent(message="Something went wrong")


@pytest.fixture
def test_display_event():
    return TestDisplayEvent(content="Display content")


@pytest.fixture
def aitl_request_event(test_start_event):
    return AgentInTheLoopRequestEvent(
        start_event=test_start_event,
        other_agent_topic=PartialAgentTopic(agent_id="agent_id", agent_class="agent_class"),
        share_thread_id=True,
    )


@pytest.fixture
def aitl_response_event(test_stop_event):
    return AgentInTheLoopResponseEvent(stop_event=test_stop_event)


@pytest.fixture
def aitl_exception_event(test_exception_event):
    return AgentInTheLoopExceptionEvent(exception_event=test_exception_event)


# ====== Helper Functions ======


def simulate_cross_process_boundary(event: BaseEvent) -> BaseEvent:
    """
    Simulates sending an event across a process boundary by:
    1. Serializing to JSON
    2. Deserializing back to an event

    This helps test the preservation of event type hierarchy.
    """
    serialized = event.model_dump_json(serialize_as_any=True)
    return BaseEvent.deserialize_event(serialized)


# ====== Tests ======


def test_event_creation(test_start_event):
    """Test that events can be created with expected attributes."""
    assert test_start_event.message == "Hello, world!"
    assert test_start_event.event_id is not None
    assert test_start_event.created_at is not None


def test_computed_type(test_start_event):
    """Test that _type property returns the correct class name."""
    assert test_start_event._event_name == "TestStartEvent"


def test_parent_event_names(test_start_event):
    """Test that _parent_event_names includes all expected parents."""
    parent_classes = test_start_event._parent_event_names
    assert "TestStartEvent" in parent_classes
    assert "StartEvent" in parent_classes
    assert "ControlEvent" in parent_classes


def test_is_properties(test_start_event, test_stop_event, test_exception_event, test_display_event):
    """Test that is_* properties correctly identify event types."""
    # Control events
    assert test_start_event.is_control_event
    assert test_start_event.is_start_event
    assert not test_start_event.is_stop_event
    assert not test_start_event.is_exception_event

    assert test_stop_event.is_control_event
    assert test_stop_event.is_stop_event
    assert not test_stop_event.is_start_event

    assert test_exception_event.is_control_event
    assert test_exception_event.is_exception_event

    # Display events
    assert test_display_event.is_display_event
    assert not test_display_event.is_control_event


def test_serialization_to_dict(test_start_event):
    """Test that events can be serialized to dictionaries."""
    data = test_start_event.model_dump()
    assert data["_event_name"] == "TestStartEvent"
    assert data["message"] == "Hello, world!"
    assert "_parent_event_names" in data
    assert "TestStartEvent" in data["_parent_event_names"]
    assert "StartEvent" in data["_parent_event_names"]


def test_serialization_to_json(test_start_event):
    """Test that events can be serialized to JSON."""
    json_str = test_start_event.model_dump_json(serialize_as_any=True)
    data = json.loads(json_str)
    assert data["_event_name"] == "TestStartEvent"
    assert data["message"] == "Hello, world!"


def test_deserialization_of_known_event(test_start_event):
    """Test that known events can be deserialized correctly."""
    json_str = test_start_event.model_dump_json(serialize_as_any=True)
    deserialized = BaseEvent.deserialize_event(json_str)
    assert isinstance(deserialized, TestStartEvent)
    assert deserialized.message == "Hello, world!"
    assert deserialized._event_name == "TestStartEvent"


def test_unknown_event_deserialization():
    """Test deserialization of an event type that isn't registered."""
    # Create a dictionary representing an event type that doesn't exist in this process
    unknown_event_data = {
        "_event_name": "UnknownEventType",
        "event_id": "12345",
        "created_at": 1234567890,
        "_parent_event_names": ["UnknownEventType", "SomeBaseClass", "AnotherBaseClass", "StartEvent", "ControlEvent"],
        "some_field": "some value",
    }

    # Deserialize it
    deserialized = BaseEvent.deserialize_event(unknown_event_data)

    # Even though we don't know this type, we should preserve its hierarchy
    assert deserialized._event_name == "UnknownEventType"
    assert "UnknownEventType" in deserialized._parent_event_names
    assert "StartEvent" in deserialized._parent_event_names
    assert deserialized.is_start_event
    assert deserialized.is_control_event
    assert not deserialized.is_stop_event

    # We should also preserve its fields
    assert deserialized.model_dump()["some_field"] == "some value"


def test_cross_process_type_checking(test_start_event, aitl_request_event):
    """
    Test that type checking works correctly even after an event crosses process boundaries.
    """
    # Simulate sending the start event across a process boundary
    remote_event = simulate_cross_process_boundary(test_start_event)

    # Type checks should still work
    assert remote_event.is_start_event
    assert remote_event.is_control_event
    assert not remote_event.is_stop_event

    # Complex event
    remote_aitl = simulate_cross_process_boundary(aitl_request_event)
    assert remote_aitl.is_aitl_request_event
    assert "AgentInTheLoopRequestEvent" in remote_aitl._parent_event_names


def test_nested_events_preservation(aitl_request_event):
    """Test that nested events preserve their type hierarchy."""
    # Simulate crossing a process boundary
    remote_aitl = simulate_cross_process_boundary(aitl_request_event)

    # The nested start event should still have its type information
    nested_start = remote_aitl.start_event
    assert nested_start.is_start_event
    assert "TestStartEvent" in nested_start._parent_event_names


def test_aitl_request_properties(aitl_request_event):
    """Test properties of AgentInTheLoopRequestEvent."""
    assert aitl_request_event.is_aitl_request_event
    assert not aitl_request_event.is_aitl_response_event
    assert not aitl_request_event.is_aitl_exception_event

    # The start event should be nested and accessible
    assert aitl_request_event.start_event.is_start_event
    assert aitl_request_event.start_event.message == "Hello, world!"


def test_aitl_response_properties(aitl_response_event):
    """Test properties of AgentInTheLoopResponseEvent."""
    assert aitl_response_event.is_aitl_response_event
    assert not aitl_response_event.is_aitl_request_event
    assert not aitl_response_event.is_aitl_exception_event

    # The stop event should be nested and accessible
    assert aitl_response_event.stop_event.is_stop_event
    assert aitl_response_event.stop_event.result == 42


def test_aitl_workflow_serialization(aitl_request_event, aitl_response_event):
    """Test a complete AITL workflow with serialization between steps."""
    # Step 1: Agent sends request to worker
    serialized_request = aitl_request_event.model_dump_json(serialize_as_any=True)

    # Step 2: Worker deserializes request
    worker_request = BaseEvent.deserialize_event(serialized_request)
    assert worker_request.is_aitl_request_event
    assert worker_request.start_event.is_start_event

    # Step 3: Worker sends response
    serialized_response = aitl_response_event.model_dump_json(serialize_as_any=True)

    # Step 4: Agent deserializes response
    agent_response = BaseEvent.deserialize_event(serialized_response)
    assert agent_response.is_aitl_response_event
    assert agent_response.stop_event.is_stop_event
    assert agent_response.stop_event.result == 42


def test_missing_fields():
    """Test deserialization with missing fields."""
    # Missing fields should be handled gracefully
    incomplete_data = {
        "_event_name": "TestStartEvent",
        # Missing message field
    }

    # This should raise a ValidationError since message is required
    with pytest.raises(Exception):
        event = BaseEvent.deserialize_event(incomplete_data)
        print(event._event_name)


def test_extra_fields():
    """Test deserialization with extra fields."""
    # Extra fields should be preserved
    extra_data = {
        "_event_name": "TestStartEvent",
        "message": "Hello",
        "agent_id": "test-agent-1",
        "extra_field": "This wasn't in the original class",
    }

    event = BaseEvent.deserialize_event(extra_data)

    # The field should be accessible in the model dump
    data = event.model_dump()
    assert data["extra_field"] == "This wasn't in the original class"

    # And directly as an attribute if we're using extra='allow'
    assert hasattr(event, "extra_field")
    assert event.extra_field == "This wasn't in the original class"

    # When re-serialized, the field should still be there
    serialized = event.model_dump_json(serialize_as_any=True)
    deserialized_again = BaseEvent.deserialize_event(serialized)
    assert deserialized_again.model_dump()["extra_field"] == "This wasn't in the original class"


def test_invalid_json():
    """Test handling of invalid JSON."""
    with pytest.raises(Exception):
        BaseEvent.deserialize_event("This is not valid JSON")


def test_corrupted_parent_event_names():
    """Test handling of corrupted _parent_event_names."""
    corrupted_data = {
        "_event_name": "TestStartEvent",
        "message": "Hello",
        "agent_id": "test-agent-1",
        "_parent_event_names": "Not a list",  # Should be a list
    }

    # Should still deserialize, but parent class info might be incorrect
    event = BaseEvent.deserialize_event(corrupted_data)
    assert event.message == "Hello"
    # Type checking should fall back to class-based hierarchy
    assert isinstance(event._parent_event_names, list)


def test_registry_contains_expected_events():
    """Test that the event registry contains expected event types."""
    registry = BaseEvent._event_registry
    assert "StartEvent" in registry
    assert "StopEvent" in registry
    assert "DisplayEvent" in registry
    assert "TestStartEvent" in registry  # Our test class should be registered


def test_duplicate_event_types_rejected():
    """Test that duplicate event type names are rejected."""
    # Attempting to create a duplicate event type should raise ValueError
    with pytest.raises(ValueError):
        # This should fail because TestStartEvent already exists
        class TestStartEvent(StartEvent):
            duplicate: str


def test_registry_is_populated_on_import():
    """Test that the registry is populated when events are imported."""
    registry = BaseEvent._event_registry
    # These should all be registered because we imported them
    assert "UserMessageEvent" in registry
    assert "AgentInTheLoopRequestEvent" in registry
    assert "LLMEvent" in registry


def test_aitl_without_worker_agent_class(aitl_response_event):
    """
    Simulates the situation where an orchestrator receives a response from a worker agent
    without having the specific WorkerStopEvent class imported.
    """
    # First serialize the response with a specific stop event
    serialized = aitl_response_event.model_dump_json(serialize_as_any=True)

    # Now remove TestStopEvent from the registry to simulate it not being available
    original_class = BaseEvent._event_registry.pop("TestStopEvent", None)
    try:
        # Deserialize without the class being available
        deserialized = BaseEvent.deserialize_event(serialized)

        # Even without the specific class, we should still be able to:

        # 1. Identify it as a response event
        assert deserialized.is_aitl_response_event

        # 2. Access the stop event (though it will be a BaseEvent)
        assert deserialized.stop_event is not None

        # 3. Know it's a stop event type
        assert deserialized.stop_event.is_stop_event

        # 4. Access its data
        assert deserialized.stop_event.model_dump()["result"] == 42
    finally:
        # Restore the class to the registry
        if original_class:
            BaseEvent._event_registry["TestStopEvent"] = original_class


def test_user_message_event_round_trip():
    """Test that a UserMessageEvent survives a round trip serialization."""
    # Create a user message
    user_msg = UserMessageEvent(message="Hello agent!", user=fake_user(), agent_id="test-agent-1")

    # Simulate crossing process boundary
    remote_msg = simulate_cross_process_boundary(user_msg)

    # Type checking should work
    assert remote_msg.is_user_message_event
    assert "UserMessageEvent" in remote_msg._parent_event_names

    # Data should be preserved
    assert remote_msg.message == "Hello agent!"


def test_llm_events_hierarchy():
    """Test that the LLM event hierarchy is preserved."""
    # Create an LLM event with a stop reason
    llm_event = LLMStopEvent(chat_model_name="test")

    # Simulate crossing process boundary
    remote_event = simulate_cross_process_boundary(llm_event)

    # Check type hierarchy
    assert remote_event.is_semantic_event  # Should be a semantic event
    assert "LLMStopEvent" in remote_event._parent_event_names
    assert "LLMEvent" in remote_event._parent_event_names

    # Data should be preserved
    assert remote_event.chat_model_name == "test"
