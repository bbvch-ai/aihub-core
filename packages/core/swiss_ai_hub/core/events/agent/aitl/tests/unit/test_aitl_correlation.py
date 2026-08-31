"""The back-reference that makes an agent-in-the-loop fan-out attributable.

A caller that delegates once can infer which answer is which. A caller that delegates N times in parallel receives N
answers on one topic, and before `request_event_id` nothing on the payload told them apart — which for the email
drafting agent would mean a reply grounded in one customer's documents appended to another customer's message.
"""

from swiss_ai_hub.core.events.agent.aitl.agent_in_the_loop import AgentInTheLoop
from swiss_ai_hub.core.events.agent.control.exception.exception_event import ExceptionEvent
from swiss_ai_hub.core.events.agent.control.start.start_event import StartEvent
from swiss_ai_hub.core.events.agent.control.stop.stop_event import StopEvent
from swiss_ai_hub.core.events.base_event import BaseEvent


def _request(agent_id: str) -> AgentInTheLoop.request:
    return AgentInTheLoop.invoke(agent_class="RAGAgent", agent_id=agent_id, start_event=StartEvent())


def test_each_request_of_a_fan_out_is_distinguishable():
    requests = [_request(f"agent-{index}") for index in range(3)]
    assert len({request.event_id for request in requests}) == 3


def test_a_response_names_the_request_it_answers():
    request = _request("agent-a")
    response = AgentInTheLoop.response(stop_event=StopEvent(), request_event_id=request.event_id)
    assert response.request_event_id == request.event_id


def test_a_failure_names_the_request_it_answers():
    """Carried on the exception too: a fan-out caller that cannot attribute a failure cannot complete its batch."""
    request = _request("agent-a")
    failure = AgentInTheLoop.exception(
        exception_event=ExceptionEvent(message="boom"), request_event_id=request.event_id
    )
    assert failure.request_event_id == request.event_id


def test_the_back_reference_survives_the_process_boundary():
    """The answer is published to NATS and read back by a different process, so the id has to be a real field."""
    request = _request("agent-a")
    response = AgentInTheLoop.response(stop_event=StopEvent(), request_event_id=request.event_id)

    revived = BaseEvent.deserialize_event(response.model_dump(serialize_as_any=True))

    assert revived.request_event_id == request.event_id


def test_a_delegation_waits_forever_unless_a_timeout_is_asked_for():
    """The default has to stay 'wait', or every existing chat-facing delegation would start failing on slow answers."""
    assert _request("agent-a").timeout_seconds is None
    assert (
        AgentInTheLoop.invoke(
            agent_class="RAGAgent", agent_id="agent-a", start_event=StartEvent(), timeout_seconds=30
        ).timeout_seconds
        == 30
    )
