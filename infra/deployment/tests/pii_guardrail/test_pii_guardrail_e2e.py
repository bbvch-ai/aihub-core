"""End-to-end tests of the pii-anonymisation guardrail through a real LiteLLM proxy and the real Presidio analyzer.

NOT part of a CI `make test` scope: they start Docker containers (analyzer, LiteLLM, echo model) on port 4199.

    uv run pytest infra/deployment/tests/pii_guardrail/ -v

The LiteLLM config is built from the generated gateway config (infra/configs/litellm), so the guardrail block under
test is the one that ships. Two echo models stand in for providers: one external, one hosted inside the deployment.
"""

import json
import re
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest
import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
OUT = HERE / "out"
RECEIVED = OUT / "received.jsonl"
PROXY = "http://localhost:4199"
MASTER_KEY = "sk-e2e"
PII = ["Reto Wyss", "756.1234.5678.97", "CH93 0076 2011 6238 5295 7", "Seefeldstrasse 18, 8008 Zürich"]
PROMPT = ("Patient Reto Wyss, AHV 756.1234.5678.97, wohnt an der Seefeldstrasse 18, 8008 Zürich. "
          "IBAN CH93 0076 2011 6238 5295 7.")
TOKEN = re.compile(r"<[A-Z][A-Z_]*_\d+>")


def image(key: str) -> str:
    tags = yaml.safe_load((REPO / "infra/deployment/compose-config.yml").read_text(encoding="utf-8"))["image_tags"]
    return f"ghcr.io/bbvch-ai/aihub-core/{tags[key]}"


def write_config() -> None:
    gateway = yaml.safe_load((REPO / "infra/configs/litellm/litellm-config.infomaniak.dev.yml").read_text(encoding="utf-8"))
    echo = {"model": "openai/echo", "api_base": "http://echo:8000/v1", "api_key": "dummy"}
    config = {
        "model_list": [
            {"model_name": "echo-external", "litellm_params": echo,
             "model_info": {"mode": "chat", "aihub_hosting_location": "swiss_cloud"}},
            {"model_name": "echo-local", "litellm_params": echo,
             "model_info": {"mode": "chat", "aihub_hosting_location": "local"}},
        ],
        "guardrails": gateway["guardrails"],
        "general_settings": {"master_key": MASTER_KEY},
    }
    OUT.mkdir(exist_ok=True)
    (OUT / "litellm-config.yml").write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")


def compose(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    env = {"ANALYZER_IMAGE": image("presidio_analyzer"), "LITELLM_IMAGE": image("litellm")}
    return subprocess.run(["docker", "compose", "-f", str(HERE / "docker-compose.yml"), *args], check=check,
                          capture_output=True, text=True, env={**__import__("os").environ, **env})


@pytest.fixture(scope="session", autouse=True)
def stack() -> Iterator[None]:
    write_config()
    RECEIVED.write_text("", encoding="utf-8")
    compose("up", "-d", "--wait", "--wait-timeout", "600")
    yield
    compose("down", check=False)


def received() -> list[list[dict]]:
    return [json.loads(line)["messages"] for line in RECEIVED.read_text(encoding="utf-8").splitlines() if line]


def chat(model: str, content: str, **extra) -> httpx.Response:
    body = {"model": model, "messages": [{"role": "user", "content": content}], **extra}
    return httpx.post(f"{PROXY}/v1/chat/completions", json=body, headers={"Authorization": f"Bearer {MASTER_KEY}"},
                      timeout=300)


def chat_stream(model: str, content: str, **extra) -> tuple[list[tuple[float, dict]], float]:
    body = {"model": model, "messages": [{"role": "user", "content": content}], "stream": True, **extra}
    started, events = time.perf_counter(), []
    with httpx.stream("POST", f"{PROXY}/v1/chat/completions", json=body, timeout=300,
                      headers={"Authorization": f"Bearer {MASTER_KEY}"}) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if line.startswith("data: ") and line != "data: [DONE]":
                events.append((time.perf_counter() - started, json.loads(line[6:])))
    return events, time.perf_counter() - started


def last_prompt_seen() -> str:
    return received()[-1][-1]["content"]


def test_should_send_placeholders_only_and_return_the_values_when_model_is_external() -> None:
    answer = chat("echo-external", PROMPT).json()["choices"][0]["message"]["content"]

    seen = last_prompt_seen()
    print(f"\nPROVIDER RECEIVED: {seen}\nUSER GOT:          {answer}")
    assert not [value for value in PII if value in seen]
    assert TOKEN.search(seen)
    assert answer == PROMPT


def test_should_stream_the_restored_answer_when_model_is_external() -> None:
    events, total = chat_stream("echo-external", PROMPT)
    texts = [(t, e["choices"][0]["delta"].get("content")) for t, e in events if e["choices"]]
    texts = [(t, text) for t, text in texts if text]

    answer = "".join(text for _, text in texts)
    print(f"\nCHUNKS: {len(texts)}, first text after {texts[0][0]:.2f} s, last after {texts[-1][0]:.2f} s")
    assert answer == PROMPT
    assert len(texts) > 5
    assert texts[0][0] < texts[-1][0]
    assert not [value for value in PII if value in last_prompt_seen()]


def test_should_keep_pronouns_and_field_labels_when_they_surround_personal_data() -> None:
    prompt = ("Sie sind ein Assistent und antworten dem Benutzer in seiner Sprache. Schreibe Ihnen eine Mahnung an "
              "Anna Muster, AHV-Nr. 756.9876.5432.10, Bahnhofstrasse 5, 3011 Bern, IBAN CH93 0076 2011 6238 5295 7. "
              "Nenne darin Name, AHV-Nummer, Adresse, Identität und IBAN.")

    answer = chat("echo-external", prompt).json()["choices"][0]["message"]["content"]

    seen = last_prompt_seen()
    print(f"\nPROVIDER RECEIVED: {seen}")
    assert seen.startswith("Sie sind ein Assistent und antworten dem Benutzer in seiner Sprache. Schreibe Ihnen")
    assert seen.endswith("Nenne darin Name, AHV-Nummer, Adresse, Identität und IBAN.")
    assert not [value for value in ["Anna Muster", "756.9876.5432.10", "3011 Bern", "CH93 0076 2011 6238 5295 7"]
                if value in seen]
    assert answer == prompt


@pytest.mark.parametrize(("address", "masked"), [("3011 Bern. Nenne", "3011 Bern"),
                                                ("9000 St. Gallen. Nenne", "9000 St. Gallen"),
                                                ("2300 La Chaux-de-Fonds. Nenne", "2300 La Chaux-de-Fonds")])
def test_should_end_the_postcode_and_city_at_the_sentence_end(address: str, masked: str) -> None:
    chat("echo-external", f"Anna Muster wohnt an der Bahnhofstrasse 5, {address} ihre Adresse.")

    seen = last_prompt_seen()
    print(f"\nPROVIDER RECEIVED: {seen}")
    assert masked not in seen
    assert re.search(r"<[A-Z_]+_\d+>\. Nenne ihre Adresse\.$", seen)


def tools() -> list[dict]:
    return [{"type": "function", "function": {"name": "lookup_patient", "description": "Find a patient",
                                              "parameters": {"type": "object",
                                                             "properties": {"query": {"type": "string"}}}}}]


def test_should_restore_tool_call_arguments_when_not_streamed() -> None:
    message = chat("echo-external", 'Suche "Reto Wyss", AHV 756.1234.5678.97', tools=tools()).json()["choices"][0]["message"]

    arguments = json.loads(message["tool_calls"][0]["function"]["arguments"])
    print(f"\nPROVIDER RECEIVED: {last_prompt_seen()}\nTOOL ARGUMENTS:    {arguments}")
    assert arguments == {"query": 'Suche "Reto Wyss", AHV 756.1234.5678.97'}
    assert "Reto Wyss" not in last_prompt_seen()


def test_should_restore_tool_call_arguments_when_streamed() -> None:
    events, _ = chat_stream("echo-external", 'Suche "Reto Wyss", AHV 756.1234.5678.97', tools=tools())

    arguments = "".join(call["function"].get("arguments") or "" for _, e in events if e["choices"]
                        for call in e["choices"][0]["delta"].get("tool_calls") or [])
    assert json.loads(arguments) == {"query": 'Suche "Reto Wyss", AHV 756.1234.5678.97'}


def test_should_not_anonymise_when_model_is_local() -> None:
    answer = chat("echo-local", PROMPT).json()["choices"][0]["message"]["content"]

    assert last_prompt_seen() == PROMPT
    assert answer == PROMPT


def test_should_anonymise_when_local_model_call_requests_the_guardrail() -> None:
    answer = chat("echo-local", PROMPT, guardrails=["pii-anonymisation"]).json()["choices"][0]["message"]["content"]

    assert not [value for value in PII if value in last_prompt_seen()]
    assert answer == PROMPT


def test_should_keep_hand_made_placeholder_when_a_new_person_is_detected() -> None:
    prompt = "Brief an <PERSON_1>, Kopie an Reto Wyss"

    answer = chat("echo-external", prompt).json()["choices"][0]["message"]["content"]

    seen = last_prompt_seen()
    print(f"\nPROVIDER RECEIVED: {seen}\nUSER GOT:          {answer}")
    assert seen.startswith("Brief an <PERSON_1>, Kopie an <")
    assert "<PERSON_1>, Kopie an <PERSON_1>" not in seen and "Reto Wyss" not in seen
    assert answer == prompt


def test_should_ship_no_builtin_presidio_guardrail_or_anonymizer() -> None:
    for config in (REPO / "infra/configs/litellm").glob("litellm-config.*.yml"):
        guardrails = yaml.safe_load(config.read_text(encoding="utf-8"))["guardrails"]
        assert [g["litellm_params"]["guardrail"] for g in guardrails] == [
            "pii_anonymisation_guardrail.PiiAnonymisationGuardrail"], config.name
    for stack in (REPO / "infra").glob("docker-compose.*.yml"):
        assert "presidio-anonymizer" not in stack.read_text(encoding="utf-8"), stack.name


def test_should_refuse_the_call_when_analyzer_is_unavailable() -> None:
    """Last: stops the analyzer for the rest of the session."""
    compose("stop", "presidio-analyzer")
    calls_before = len(received())

    response = chat("echo-external", PROMPT)

    print(f"\nHTTP {response.status_code}: {response.text[:300]}")
    assert response.status_code >= 400
    assert "PII anonymisation is unavailable" in response.text
    assert len(received()) == calls_before  # nothing reached the provider
