import asyncio

import pytest

from swiss_ai_hub.core.generative_ai.resources.models.llm.gateway_guardrails import GatewayGuardrails

PII = GatewayGuardrails.PII_ANONYMISATION


def test_should_request_nothing_outside_a_block() -> None:
    assert GatewayGuardrails.requested() == ()
    assert not GatewayGuardrails.anonymising()


def test_should_request_the_guardrail_inside_a_block_and_drop_it_after() -> None:
    with GatewayGuardrails.requesting(PII):
        assert GatewayGuardrails.anonymising()

    assert GatewayGuardrails.requested() == ()


def test_should_keep_the_outer_guardrails_in_a_nested_block_without_duplicates() -> None:
    with GatewayGuardrails.requesting(PII), GatewayGuardrails.requesting("other", PII):
        assert GatewayGuardrails.requested() == (PII, "other")


def test_should_request_nothing_when_a_block_names_nothing() -> None:
    with GatewayGuardrails.requesting():
        assert GatewayGuardrails.requested() == ()


@pytest.mark.asyncio
async def test_should_reach_tasks_and_threads_started_inside_the_block() -> None:
    with GatewayGuardrails.requesting(PII):
        in_task = await asyncio.create_task(asyncio.sleep(0, result=GatewayGuardrails.anonymising()))
        in_thread = await asyncio.to_thread(GatewayGuardrails.anonymising)

    assert in_task
    assert in_thread


def test_should_add_the_guardrails_to_the_extra_body_and_keep_what_it_carries() -> None:
    kwargs = {"model": "m", "extra_body": {"chat_template_kwargs": {"thinking": False}, "guardrails": ["other"]}}

    merged = GatewayGuardrails.merged_into(kwargs, (PII,))

    assert merged["extra_body"] == {"chat_template_kwargs": {"thinking": False}, "guardrails": ["other", PII]}
    assert kwargs["extra_body"]["guardrails"] == ["other"]


def test_should_leave_the_request_unchanged_when_nothing_is_requested() -> None:
    kwargs = {"model": "m"}

    assert GatewayGuardrails.merged_into(kwargs) is kwargs
