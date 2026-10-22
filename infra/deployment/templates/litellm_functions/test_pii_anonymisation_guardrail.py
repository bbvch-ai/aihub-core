"""Unit tests for pii_anonymisation_guardrail.py, with LiteLLM's own types and a fake analyzer.

NOT part of a CI `make test` scope (see test_custom_callbacks.py). Run them with the LiteLLM version the gateway runs:

    uv run --with "litellm==1.83.10" pytest infra/deployment/templates/litellm_functions/test_pii_anonymisation_guardrail.py

The live end-to-end tests through a LiteLLM proxy are in infra/deployment/tests/pii_guardrail_e2e/.
"""

import asyncio
import importlib.util
import json
import re
import sys
import types
from pathlib import Path

import httpx
import pytest
from litellm.types.utils import (
    ChatCompletionDeltaToolCall,
    ChatCompletionMessageToolCall,
    Choices,
    Delta,
    Function,
    Message,
    ModelResponse,
    ModelResponseStream,
    StreamingChoices,
)

MODULE_PATH = Path(__file__).parent / "pii_anonymisation_guardrail.py"
KNOWN_PII = {"Reto Wyss": "PERSON", "Anna Muster": "PERSON", "756.1234.5678.97": "NATIONAL_ID",
             "CH93 0076 2011 6238 5295 7": "IBAN_CODE", "Seefeldstrasse 18": "CH_ADDRESS",
             "Seefeldstrasse 18, 8008 Zürich": "CH_ADDRESS", "O\"Brien Sean": "PERSON"}


def load_module():
    # The guardrail imports its audit module by name, as LiteLLM's /app holds both files.
    sys.path.insert(0, str(MODULE_PATH.parent))
    sys.modules.pop("pii_anonymisation_guardrail", None)
    spec = importlib.util.spec_from_file_location("pii_anonymisation_guardrail", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guardrail_module = load_module()


def fake_spans(text: str) -> list[dict]:
    """Every occurrence of every known value, overlapping ones included, as Presidio would return them."""
    return [{"start": m.start(), "end": m.end(), "entity_type": entity, "score": 1.0}
            for value, entity in KNOWN_PII.items() for m in re.finditer(re.escape(value), text)]


def bare_guardrail(**settings):
    """A guardrail on the real analyzer client, for the model the test requests (no router in unit tests)."""
    guardrail = guardrail_module.PiiAnonymisationGuardrail(
        guardrail_name="pii-anonymisation", event_hook=["pre_call", "post_call"], default_on=False, **settings)
    guardrail._external["external-model"] = True
    return guardrail


def make_guardrail(external: dict[str, bool] | None = None):
    guardrail = guardrail_module.PiiAnonymisationGuardrail(
        guardrail_name="pii-anonymisation", event_hook=["pre_call", "post_call"], default_on=False,
        presidio_language="de", pii_entities_config={"PERSON": "MASK", "NATIONAL_ID": "MASK"})
    guardrail.analyzed: list[dict] = []

    async def analyze(text: str) -> list[dict]:
        guardrail.analyzed.append({"text": text, "language": guardrail.language})
        return fake_spans(text)

    guardrail.analyze = analyze
    guardrail._external.update(external or {"external-model": True, "local-model": False})
    return guardrail


def run(coroutine):
    return asyncio.run(coroutine)


async def mask(guardrail, data: dict) -> dict:
    return await guardrail.async_pre_call_hook(None, None, data, "acompletion")


def request(content, **extra) -> dict:
    return {"model": "external-model", "messages": [{"role": "user", "content": content}], "litellm_call_id": "call-1",
            **extra}


def response(content=None, tool_arguments=None, reasoning=None) -> ModelResponse:
    tool_calls = None
    if tool_arguments is not None:
        tool_calls = [ChatCompletionMessageToolCall(id="t1", type="function",
                                                    function=Function(name="lookup", arguments=tool_arguments))]
    message = Message(content=content, tool_calls=tool_calls, reasoning_content=reasoning)
    return ModelResponse(choices=[Choices(index=0, message=message, finish_reason="stop")])


def stream_chunks(pieces: list[str], field: str = "content") -> list[ModelResponseStream]:
    chunks = []
    for number, piece in enumerate(pieces):
        finish = "stop" if number == len(pieces) - 1 else None
        delta = Delta(tool_calls=[ChatCompletionDeltaToolCall(index=0, function=Function(arguments=piece))]) \
            if field == "tool" else Delta(**{field: piece})
        chunks.append(ModelResponseStream(choices=[StreamingChoices(index=0, delta=delta, finish_reason=finish)]))
    return chunks


async def collect(guardrail, chunks: list[ModelResponseStream], data: dict, field: str = "content") -> list[str]:
    async def upstream():
        for chunk in chunks:
            yield chunk

    out = []
    async for chunk in guardrail.async_post_call_streaming_iterator_hook(None, upstream(), data):
        delta = chunk.choices[0].delta
        if field == "tool":
            out.append("".join(t.function.arguments or "" for t in delta.tool_calls or []))
        else:
            out.append(getattr(delta, field) or "")
    return out


def split_every(text: str, size: int) -> list[str]:
    return [text[i:i + size] for i in range(0, len(text), size)]


# ---------------------------------------------------------------- the provider sees placeholders, the user the values

def test_should_send_placeholders_only_when_request_has_pii() -> None:
    guardrail = make_guardrail()
    data = run(mask(guardrail, request("Patient Reto Wyss, AHV 756.1234.5678.97, IBAN CH93 0076 2011 6238 5295 7")))

    sent = data["messages"][0]["content"]

    assert sent == "Patient <PERSON_1>, AHV <NATIONAL_ID_2>, IBAN <IBAN_CODE_3>"
    assert not any(value in sent for value in KNOWN_PII)


def test_should_restore_values_when_answer_is_not_streamed() -> None:
    guardrail = make_guardrail()
    data = run(mask(guardrail, request("Patient Reto Wyss, AHV 756.1234.5678.97")))

    result = run(guardrail.async_post_call_success_hook(data, None, response("Hallo <PERSON_1> (<NATIONAL_ID_2>)")))

    assert result.choices[0].message.content == "Hallo Reto Wyss (756.1234.5678.97)"


def test_should_restore_every_message_role_with_one_map_per_request() -> None:
    guardrail = make_guardrail()
    data = {"model": "external-model", "litellm_call_id": "c", "messages": [
        {"role": "system", "content": "Kunde: Reto Wyss"}, {"role": "user", "content": "Ruf Reto Wyss an"},
        {"role": "assistant", "content": "Gerne, Anna Muster"}, {"role": "tool", "content": "AHV 756.1234.5678.97"}]}

    run(mask(guardrail, data))

    assert [m["content"] for m in data["messages"]] == ["Kunde: <PERSON_1>", "Ruf <PERSON_1> an", "Gerne, <PERSON_2>",
                                                        "AHV <NATIONAL_ID_3>"]


def test_should_mask_text_parts_only_when_message_has_image() -> None:
    guardrail = make_guardrail()
    image = {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}}
    data = run(mask(guardrail, request([{"type": "text", "text": "Das ist Reto Wyss"}, image])))

    assert data["messages"][0]["content"] == [{"type": "text", "text": "Das ist <PERSON_1>"}, image]


# ---------------------------------------------------------------- streaming

@pytest.mark.parametrize("piece_size", [1, 2, 3, 5, 8])
def test_should_restore_placeholders_when_split_across_chunks(piece_size: int) -> None:
    guardrail = make_guardrail()
    data = run(mask(guardrail, request("Patient Reto Wyss, AHV 756.1234.5678.97", stream=True)))
    answer = "Der Patient <PERSON_1> hat die AHV <NATIONAL_ID_2>. Bitte <PERSON_1> anrufen."

    out = run(collect(guardrail, stream_chunks(split_every(answer, piece_size)), data))

    assert "".join(out) == "Der Patient Reto Wyss hat die AHV 756.1234.5678.97. Bitte Reto Wyss anrufen."


def test_should_stream_text_before_the_answer_ends() -> None:
    guardrail = make_guardrail()
    data = run(mask(guardrail, request("Patient Reto Wyss", stream=True)))

    out = run(collect(guardrail, stream_chunks(["Guten Tag ", "<PERS", "ON_1>", ", wie geht's?"]), data))

    assert out[0] == "Guten Tag "  # sent on at once, not buffered until the end
    assert out[1] == ""  # only the possible placeholder prefix is held back
    assert "".join(out) == "Guten Tag Reto Wyss, wie geht's?"


def test_should_restore_reasoning_when_streamed() -> None:
    guardrail = make_guardrail()
    data = run(mask(guardrail, request("Patient Reto Wyss", stream=True)))

    out = run(collect(guardrail, stream_chunks(["Ich denke an <PER", "SON_1>"], "reasoning_content"), data,
                      "reasoning_content"))

    assert "".join(out) == "Ich denke an Reto Wyss"


# ---------------------------------------------------------------- tool calls and structured output

def test_should_restore_tool_call_arguments_as_valid_json_when_not_streamed() -> None:
    guardrail = make_guardrail()
    data = run(mask(guardrail, request('Find O"Brien Sean and Reto Wyss')))

    result = run(guardrail.async_post_call_success_hook(
        data, None, response(tool_arguments='{"name": "<PERSON_1>", "other": "<PERSON_2>"}')))

    assert json.loads(result.choices[0].message.tool_calls[0].function.arguments) == {"name": 'O"Brien Sean',
                                                                                      "other": "Reto Wyss"}


@pytest.mark.parametrize("piece_size", [1, 4, 9])
def test_should_restore_tool_call_arguments_as_valid_json_when_streamed(piece_size: int) -> None:
    guardrail = make_guardrail()
    data = run(mask(guardrail, request('Find O"Brien Sean', stream=True)))

    out = run(collect(guardrail, stream_chunks(split_every('{"name": "<PERSON_1>"}', piece_size), "tool"), data, "tool"))

    assert json.loads("".join(out)) == {"name": 'O"Brien Sean'}


def test_should_keep_structured_json_output_valid_when_value_has_a_quote() -> None:
    guardrail = make_guardrail()
    data = run(mask(guardrail, request('Find O"Brien Sean', response_format={"type": "json_object"})))

    result = run(guardrail.async_post_call_success_hook(data, None, response('{"person": "<PERSON_1>"}')))

    assert json.loads(result.choices[0].message.content) == {"person": 'O"Brien Sean'}


# ---------------------------------------------------------------- overlaps and hand-anonymised input

def test_should_never_break_a_placeholder_when_detections_overlap() -> None:
    guardrail = make_guardrail()
    data = run(mask(guardrail, request("Adresse: Seefeldstrasse 18, 8008 Zürich")))

    assert data["messages"][0]["content"] == "Adresse: <CH_ADDRESS_1>"
    result = run(guardrail.async_post_call_success_hook(data, None, response("Wohnt an <CH_ADDRESS_1>.")))
    assert result.choices[0].message.content == "Wohnt an Seefeldstrasse 18, 8008 Zürich."


def test_should_keep_hand_made_placeholder_and_give_new_person_another_one() -> None:
    guardrail = make_guardrail()
    data = run(mask(guardrail, request("Brief an <PERSON_1>, Kopie an Reto Wyss")))

    sent = data["messages"][0]["content"]
    result = run(guardrail.async_post_call_success_hook(data, None, response("<PERSON_1> und <PERSON_2>")))

    assert sent == "Brief an <PERSON_1>, Kopie an <PERSON_2>"
    assert result.choices[0].message.content == "<PERSON_1> und Reto Wyss"


def test_should_not_detect_inside_a_hand_made_placeholder() -> None:
    guardrail = make_guardrail()

    async def analyze(text: str) -> list[dict]:
        return [{"start": text.index("<PERSON_1>"), "end": text.index("<PERSON_1>") + 10, "entity_type": "PERSON",
                 "score": 0.6}]

    guardrail.analyze = analyze
    data = run(mask(guardrail, request("Brief an <PERSON_1>")))

    assert data["messages"][0]["content"] == "Brief an <PERSON_1>"


# ---------------------------------------------------------------- which calls are anonymised

def test_should_run_when_model_is_external() -> None:
    assert make_guardrail().should_run_guardrail(request("x"), guardrail_module.GuardrailEventHooks.pre_call)


def test_should_not_run_when_model_is_local_and_not_requested() -> None:
    data = {**request("x"), "model": "local-model"}

    assert not make_guardrail().should_run_guardrail(data, guardrail_module.GuardrailEventHooks.pre_call)


def test_should_run_when_local_model_requests_the_guardrail_by_name() -> None:
    data = {**request("x"), "model": "local-model", "guardrails": ["pii-anonymisation"]}

    assert make_guardrail().should_run_guardrail(data, guardrail_module.GuardrailEventHooks.pre_call)


def test_should_not_run_when_call_is_not_a_chat() -> None:
    data = {"model": "external-model", "input": ["Reto Wyss"]}

    assert not make_guardrail().should_run_guardrail(data, guardrail_module.GuardrailEventHooks.pre_call)


@pytest.mark.parametrize(("locations", "external"), [(["local"], False), (["swiss_cloud"], True), ([None], True),
                                                     (["local", "swiss_cloud"], True), ([], True)])
def test_should_read_hosting_location_from_model_info(monkeypatch, locations: list, external: bool) -> None:
    router = types.SimpleNamespace(get_model_list=lambda model_name: [
        {"model_name": model_name, "model_info": {"aihub_hosting_location": loc} if loc else {}} for loc in locations])
    monkeypatch.setitem(sys.modules, "litellm.proxy.proxy_server", types.SimpleNamespace(llm_router=router))
    guardrail = make_guardrail(external={})

    assert guardrail.is_external("some-model") is external


# ---------------------------------------------------------------- failure, language, map handling

def test_should_refuse_the_call_when_analyzer_is_unavailable() -> None:
    guardrail = bare_guardrail()
    guardrail.analyze_url = "http://127.0.0.1:9/analyze"  # nothing listens on the discard port
    data = request("Patient Reto Wyss")

    with pytest.raises(guardrail_module.AnonymisationUnavailableError, match="not sent"):
        run(mask(guardrail, data))
    assert data["messages"][0]["content"] == "Patient Reto Wyss"  # untouched, and the call does not proceed


def test_should_refuse_the_call_when_analyzer_answers_with_an_error(monkeypatch) -> None:
    guardrail = bare_guardrail()
    guardrail.client = httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(401)))

    with pytest.raises(guardrail_module.AnonymisationUnavailableError):
        run(mask(guardrail, request("Patient Reto Wyss")))


def test_should_analyse_in_de_when_request_hints_another_language() -> None:
    guardrail = make_guardrail()

    run(mask(guardrail, request("Patient Reto Wyss", guardrail_config={"language": "en"})))

    assert {call["language"] for call in guardrail.analyzed} == {"de"}


# ---------------------------------------------------------------- allow-list

# How the analyzer applies an allow-list in regex mode: its default flags, then search() on each detected span.
PRESIDIO_REGEX_FLAGS = re.DOTALL | re.MULTILINE | re.IGNORECASE


def guardrail_capturing_requests(allow_list: list[str] | None) -> tuple:
    sent: list[dict] = []
    guardrail = bare_guardrail(pii_allow_list=allow_list)

    def answer(analyzer_request: httpx.Request) -> httpx.Response:
        sent.append(json.loads(analyzer_request.content))
        return httpx.Response(200, json=[])

    guardrail.client = httpx.AsyncClient(transport=httpx.MockTransport(answer))
    return guardrail, sent


def test_should_send_the_allow_list_with_every_analysis_when_configured() -> None:
    guardrail, sent = guardrail_capturing_requests(["Sie", "Adresse"])

    run(mask(guardrail, request("Sie wohnen an der Adresse Seefeldstrasse 18")))

    assert sent[0]["allow_list_match"] == "regex"
    assert len(sent[0]["allow_list"]) == 1


def test_should_send_no_allow_list_when_none_is_configured() -> None:
    guardrail, sent = guardrail_capturing_requests(None)

    run(mask(guardrail, request("Patient Reto Wyss")))

    assert "allow_list" not in sent[0]


@pytest.mark.parametrize("span", ["Sie", "SIE", "sie", "Adresse", "AHV-Nr.", "date de naissance"])
def test_should_allow_a_span_that_is_exactly_an_allowed_word_in_any_case(span: str) -> None:
    pattern = guardrail_module.PiiAnonymisationGuardrail.allow_list_pattern(
        ["Sie", "Adresse", "AHV-Nr.", "date de naissance"])

    assert re.compile(pattern, PRESIDIO_REGEX_FLAGS).search(span)


@pytest.mark.parametrize("span", ["Siegfried", "Sie Anna Muster", "Sie\nAnna Muster", "Anna Muster\nSie",
                                  "AHV-Nrx", "Adressen"])
def test_should_keep_masking_a_span_that_only_contains_an_allowed_word(span: str) -> None:
    pattern = guardrail_module.PiiAnonymisationGuardrail.allow_list_pattern(["Sie", "Adresse", "AHV-Nr."])

    assert not re.compile(pattern, PRESIDIO_REGEX_FLAGS).search(span)


@pytest.mark.parametrize("span", ["Position 2", "position 12a", "Art. 5", "Artikel Nr. 3", "Position\n4"])
def test_should_allow_a_numbered_label(span: str) -> None:
    pattern = guardrail_module.PiiAnonymisationGuardrail.allow_list_pattern(["Position", "Art.", "Artikel"])

    assert re.compile(pattern, PRESIDIO_REGEX_FLAGS).search(span)


@pytest.mark.parametrize("span", ["Position 12345", "Position 2 Anna Muster", "Art. 756.1234.5678.97",
                                  "Position 044 270 41 87"])
def test_should_keep_masking_a_label_followed_by_more_than_a_short_number(span: str) -> None:
    pattern = guardrail_module.PiiAnonymisationGuardrail.allow_list_pattern(["Position", "Art."])

    assert not re.compile(pattern, PRESIDIO_REGEX_FLAGS).search(span)


def test_should_send_no_allow_list_when_it_holds_only_blanks() -> None:
    assert guardrail_module.PiiAnonymisationGuardrail.allow_list_pattern(["", "  "]) is None


def test_should_keep_the_map_out_of_request_metadata() -> None:
    guardrail = make_guardrail()

    data = run(mask(guardrail, request("Patient Reto Wyss", metadata={"tags": ["thread_id:1"]})))

    assert "Reto Wyss" not in json.dumps(data["metadata"])
    assert "Reto Wyss" not in json.dumps({k: v for k, v in data.items() if k != "messages"})


def test_should_drop_the_map_when_the_call_ends() -> None:
    guardrail = make_guardrail()
    data = run(mask(guardrail, request("Patient Reto Wyss")))
    run(guardrail.async_post_call_success_hook(data, None, response("<PERSON_1>")))
    streamed = run(mask(guardrail, request("Patient Reto Wyss", stream=True, litellm_call_id="call-2")))
    run(collect(guardrail, stream_chunks(["<PERSON_1>"]), streamed))
    failed = run(mask(guardrail, request("Patient Reto Wyss", litellm_call_id="call-3")))
    run(guardrail.async_post_call_failure_hook(failed, Exception("boom"), None))

    assert guardrail._maps == {}
