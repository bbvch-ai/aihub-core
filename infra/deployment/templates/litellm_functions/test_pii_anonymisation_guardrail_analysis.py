"""Unit tests for how the guardrail spends analyzer time: the text cache, parallel analysis and the timeout.

Run with the other guardrail tests (see test_pii_anonymisation_guardrail.py for the command).
"""

import asyncio
import json

import httpx
import pytest
from test_pii_anonymisation_guardrail import bare_guardrail, fake_spans, guardrail_module, make_guardrail, mask, run

SYSTEM_PROMPT = "Du bist ein Assistent der Klinik."


def conversation(turns: int) -> dict:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in range(turns):
        messages += [{"role": "user", "content": f"Frage {turn} zu Patient Reto Wyss"},
                     {"role": "assistant", "content": f"Antwort {turn}: AHV 756.1234.5678.97"}]
    messages.append({"role": "user", "content": f"Frage {turns} zu Patient Reto Wyss"})
    return {"model": "external-model", "messages": messages, "litellm_call_id": f"call-{turns}"}


def analyzer_counting_requests(**settings) -> tuple:
    sent: list[str] = []
    guardrail = bare_guardrail(**settings)

    def answer(analyzer_request: httpx.Request) -> httpx.Response:
        text = json.loads(analyzer_request.content)["text"]
        sent.append(text)
        return httpx.Response(200, json=fake_spans(text))

    guardrail.client = httpx.AsyncClient(transport=httpx.MockTransport(answer))
    return guardrail, sent


# ---------------------------------------------------------------- text cache

def test_should_analyse_only_the_new_texts_when_a_conversation_continues() -> None:
    guardrail, sent = analyzer_counting_requests()
    run(mask(guardrail, conversation(2)))
    sent.clear()

    run(mask(guardrail, conversation(3)))

    assert sent == ["Antwort 2: AHV 756.1234.5678.97", "Frage 3 zu Patient Reto Wyss"]


def test_should_mask_a_cached_text_exactly_as_a_freshly_analysed_one() -> None:
    guardrail, _ = analyzer_counting_requests()
    first = run(mask(guardrail, conversation(1)))

    second = run(mask(guardrail, conversation(1)))

    assert second["messages"] == first["messages"]


def test_should_analyse_a_text_repeated_within_one_call_once() -> None:
    guardrail, sent = analyzer_counting_requests()
    data = {"model": "external-model", "litellm_call_id": "call-1",
            "messages": [{"role": "user", "content": "Patient Reto Wyss"},
                         {"role": "user", "content": "Patient Reto Wyss"}]}

    masked = run(mask(guardrail, data))

    assert sent == ["Patient Reto Wyss"]
    assert [m["content"] for m in masked["messages"]] == ["Patient <PERSON_1>", "Patient <PERSON_1>"]


def test_should_keep_no_text_in_the_cache() -> None:
    guardrail, _ = analyzer_counting_requests()

    run(mask(guardrail, conversation(1)))

    stored = json.dumps(list(guardrail.cache._entries.items()))
    assert "Reto Wyss" not in stored
    assert "756.1234.5678.97" not in stored


def test_should_analyse_again_when_the_cached_spans_have_expired() -> None:
    guardrail, sent = analyzer_counting_requests()
    guardrail.cache.ttl_seconds = -1
    run(mask(guardrail, conversation(0)))
    sent.clear()

    run(mask(guardrail, conversation(0)))

    assert len(sent) == 2


def test_should_drop_the_least_recently_used_text_when_the_cache_is_full() -> None:
    cache = guardrail_module.AnalysisCache(ttl_seconds=60, max_texts=2)
    cache.put("a", [])
    cache.put("b", [])
    cache.get("a")

    cache.put("c", [])

    assert cache.get("b") is None
    assert cache.get("a") == []


def test_should_not_cache_a_failed_analysis() -> None:
    guardrail = bare_guardrail()
    guardrail.client = httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(503)))

    with pytest.raises(guardrail_module.AnonymisationUnavailableError):
        run(mask(guardrail, conversation(0)))

    assert not guardrail.cache._entries


# ---------------------------------------------------------------- parallel analysis

def test_should_analyse_at_most_the_per_call_limit_of_texts_at_once() -> None:
    guardrail = make_guardrail()
    in_flight, peak = 0, 0

    async def analyze(text: str) -> list[dict]:
        nonlocal in_flight, peak
        in_flight += 1
        peak = max(peak, in_flight)
        await asyncio.sleep(0.01)
        in_flight -= 1
        return fake_spans(text)

    guardrail.analyze = analyze
    run(mask(guardrail, conversation(5)))

    assert peak == guardrail_module.PARALLEL_ANALYSES_PER_CALL


def test_should_number_placeholders_in_message_order_whatever_order_the_analyses_finish() -> None:
    guardrail = make_guardrail()
    data = {"model": "external-model", "litellm_call_id": "call-1",
            "messages": [{"role": "user", "content": "Brief an Reto Wyss"},
                         {"role": "user", "content": "Kopie an Anna Muster"}]}

    async def analyze(text: str) -> list[dict]:
        await asyncio.sleep(0.05 if "Reto" in text else 0)
        return fake_spans(text)

    guardrail.analyze = analyze
    masked = run(mask(guardrail, data))

    assert [m["content"] for m in masked["messages"]] == ["Brief an <PERSON_1>", "Kopie an <PERSON_2>"]


def test_should_stop_the_other_analyses_and_refuse_when_one_fails() -> None:
    guardrail = make_guardrail()
    finished: list[str] = []

    async def analyze(text: str) -> list[dict]:
        if "Frage 0" in text:
            raise guardrail_module.AnonymisationUnavailableError("analyzer down")
        await asyncio.sleep(0.05)
        finished.append(text)
        return fake_spans(text)

    guardrail.analyze = analyze

    with pytest.raises(guardrail_module.AnonymisationUnavailableError):
        run(mask(guardrail, conversation(3)))
    assert not finished


# ---------------------------------------------------------------- timeout

@pytest.mark.parametrize(("value", "seconds"), [(None, 150.0), ("", 150.0), ("300", 300.0), (" 45.5 ", 45.5)])
def test_should_read_the_analyzer_timeout_from_the_environment(monkeypatch, value: str | None,
                                                               seconds: float) -> None:
    if value is None:
        monkeypatch.delenv("PRESIDIO_ANALYZER_TIMEOUT_SECONDS", raising=False)
    else:
        monkeypatch.setenv("PRESIDIO_ANALYZER_TIMEOUT_SECONDS", value)

    guardrail = guardrail_module.PiiAnonymisationGuardrail(guardrail_name="pii-anonymisation")

    assert guardrail.client.timeout.read == seconds


@pytest.mark.parametrize("value", ["abc", "0", "-5", "nan", "inf"])
def test_should_fall_back_to_the_default_timeout_when_the_value_is_unusable(monkeypatch, caplog, value: str) -> None:
    monkeypatch.setenv("PRESIDIO_ANALYZER_TIMEOUT_SECONDS", value)

    guardrail = guardrail_module.PiiAnonymisationGuardrail(guardrail_name="pii-anonymisation")

    assert guardrail.client.timeout.read == guardrail_module.DEFAULT_ANALYZER_TIMEOUT_SECONDS
    assert "PRESIDIO_ANALYZER_TIMEOUT_SECONDS must be a positive number" in caplog.text
