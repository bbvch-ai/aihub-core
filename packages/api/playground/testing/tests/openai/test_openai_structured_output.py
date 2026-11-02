"""Structured output from agents through the official OpenAI SDK: `response_format` and forced function calls."""

import json

import httpx
import openai
import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport
from pydantic import BaseModel
from swiss_ai_hub.core.events.agent import ChunkEvent, LLMCostEvent, LLMStopEvent, Message, RefusalReason, RefusalStopEvent
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler

from swiss_ai_hub.api.routes.openai.openai_controller import OpenaiController
from swiss_ai_hub.api.runners.simulation.agent.simulated_agent_api_test_runner import SimulatedAgentApiTestRunner

AGENT_CLASS = "structured_agent"
AGENT_ID = "structured_agent_1"
MODEL = f"{AGENT_CLASS}/{AGENT_ID}"
INVOICE = {"issuer": "ACME AG", "total": 120.5, "lines": [{"item": "Bolts", "amount": 120.5}]}
EXTRACT_INVOICE = {
    "type": "function",
    "function": {
        "name": "extract_invoice",
        "description": "Record the invoice's header.",
        "parameters": {
            "type": "object",
            "properties": {"issuer": {"type": "string"}, "total": {"type": ["number", "null"]}},
            "required": ["issuer", "total"],
        },
    },
}
FORCE_EXTRACT_INVOICE = {"type": "function", "function": {"name": "extract_invoice"}}


class Line(BaseModel):
    item: str
    amount: float


class Invoice(BaseModel):
    issuer: str
    total: float | None
    lines: list[Line]


def _answering(structured: dict | None, text: str | None = None) -> list:
    """What an agent publishes: the JSON streamed as chunks, its cost, and the stop event carrying the result."""
    content = text if structured is None else json.dumps(structured)
    stop = LLMStopEvent(output_messages=[Message.from_string(role="assistant", content=content)])
    stop.structured_output = structured
    return [
        ChunkEvent(content=content, model_name="gpt-4"),
        LLMCostEvent(
            llm_name="gpt-4",
            prompt_token_count=9,
            completion_token_count=15,
            embedding_token_count=0,
            prompt_tokens_costs=0.1,
            completion_tokens_costs=0.3,
            embedding_tokens_costs=0.0,
        ),
        stop,
    ]


@pytest_asyncio.fixture
async def agent():
    controller = OpenaiController(auth=TestAuthHandler()).chat_completion_with_assistants()
    runner = SimulatedAgentApiTestRunner(agent_class=AGENT_CLASS, agent_id=AGENT_ID, supports_response_schema=True)
    runner.simulated_events = _answering(INVOICE)
    runner.mount(controller)
    await runner.start_simulation()
    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        runner.create_agent_config_in_db()
        client = openai.AsyncOpenAI(
            api_key="unused",
            base_url="http://test/api/v1/active/openai",
            http_client=httpx.AsyncClient(transport=ASGITransport(app=lifespan.app)),
            max_retries=0,
        )
        yield client, runner
    await runner.stop_simulation()


def _requested_schema(runner: SimulatedAgentApiTestRunner):
    return next(event for event in runner.received_events if event.is_user_message_event).response_schema


@pytest.mark.asyncio
async def test_parse_with_a_pydantic_model_returns_the_parsed_answer(agent):
    client, runner = agent

    completion = await client.chat.completions.parse(
        model=MODEL, messages=[{"role": "user", "content": "Extract the invoice."}], response_format=Invoice
    )

    assert completion.choices[0].message.parsed == Invoice.model_validate(INVOICE)
    assert completion.choices[0].finish_reason == "stop"
    assert completion.usage.prompt_tokens == 9
    schema = _requested_schema(runner)
    assert schema.name == "Invoice"
    assert schema.strict is True
    assert schema.json_schema["required"] == ["issuer", "total", "lines"]


@pytest.mark.asyncio
async def test_a_streamed_parse_ends_with_the_parsed_answer_not_the_streamed_attempt(agent):
    client, runner = agent
    runner.simulated_events = [ChunkEvent(content="not json", model_name="gpt-4"), *_answering(INVOICE)[1:]]

    async with client.chat.completions.stream(
        model=MODEL, messages=[{"role": "user", "content": "Extract the invoice."}], response_format=Invoice
    ) as stream:
        completion = await stream.get_final_completion()

    assert completion.choices[0].message.parsed == Invoice.model_validate(INVOICE)


@pytest.mark.asyncio
async def test_json_object_mode_asks_for_any_object(agent):
    client, runner = agent

    completion = await client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "Extract the invoice as JSON."}],
        response_format={"type": "json_object"},
    )

    assert json.loads(completion.choices[0].message.content) == INVOICE
    assert _requested_schema(runner).json_schema is None


@pytest.mark.asyncio
async def test_a_forced_function_returns_the_answer_as_its_arguments(agent):
    client, runner = agent
    runner.simulated_events = _answering({"issuer": "ACME AG", "total": None})

    completion = await client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "Extract the invoice."}],
        tools=[EXTRACT_INVOICE],
        tool_choice=FORCE_EXTRACT_INVOICE,
    )

    choice = completion.choices[0]
    assert choice.finish_reason == "tool_calls"
    assert choice.message.content is None
    assert choice.message.tool_calls[0].function.name == "extract_invoice"
    assert json.loads(choice.message.tool_calls[0].function.arguments) == {"issuer": "ACME AG", "total": None}
    schema = _requested_schema(runner)
    assert schema.description == "Record the invoice's header."
    assert schema.json_schema == EXTRACT_INVOICE["function"]["parameters"]


@pytest.mark.asyncio
async def test_a_streamed_forced_function_arrives_as_one_tool_call_delta(agent):
    client, _ = agent

    stream = await client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "Extract the invoice."}],
        tools=[EXTRACT_INVOICE],
        tool_choice=FORCE_EXTRACT_INVOICE,
        stream=True,
    )
    chunks = [chunk async for chunk in stream]

    calls = [call for chunk in chunks for choice in chunk.choices for call in choice.delta.tool_calls or []]
    assert [call.function.name for call in calls] == ["extract_invoice"]
    assert json.loads(calls[0].function.arguments) == INVOICE
    assert chunks[-1].choices[0].finish_reason == "tool_calls"


@pytest.mark.asyncio
async def test_a_turn_without_the_json_comes_back_as_a_refusal(agent):
    client, runner = agent
    stop = RefusalStopEvent(
        reason=RefusalReason.INPUT_TOO_LARGE,
        output_messages=[Message.from_string(role="assistant", content="The file is too large.")],
    )
    runner.simulated_events = [stop]

    completion = await client.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": "Extract."}], response_format={"type": "json_object"}
    )

    assert completion.choices[0].message.content is None
    assert completion.choices[0].message.refusal == "The file is too large."


@pytest.mark.asyncio
async def test_an_agent_without_support_is_refused_before_it_is_called(agent):
    client, runner = agent
    runner.supports_response_schema = False
    runner.create_agent_config_in_db()

    with pytest.raises(openai.BadRequestError) as refused:
        await client.chat.completions.parse(
            model=MODEL, messages=[{"role": "user", "content": "Extract."}], response_format=Invoice
        )

    assert refused.value.body["param"] == "response_format"
    assert "does not support structured output" in refused.value.body["message"]
    assert not runner.received_events


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tools", "tool_choice", "param"),
    [
        ([EXTRACT_INVOICE], "auto", "tool_choice"),
        ([EXTRACT_INVOICE], openai.NOT_GIVEN, "tool_choice"),
        ([EXTRACT_INVOICE, {**EXTRACT_INVOICE, "function": {"name": "other"}}], FORCE_EXTRACT_INVOICE, "tools"),
    ],
    ids=["auto", "unforced", "several-tools"],
)
async def test_caller_tools_the_agent_would_have_to_run_are_refused(agent, tools, tool_choice, param):
    client, runner = agent

    with pytest.raises(openai.BadRequestError) as refused:
        await client.chat.completions.create(
            model=MODEL, messages=[{"role": "user", "content": "Extract."}], tools=tools, tool_choice=tool_choice
        )

    assert refused.value.body["param"] == param
    assert "do not call caller tools" in refused.value.body["message"]
    assert not runner.received_events
