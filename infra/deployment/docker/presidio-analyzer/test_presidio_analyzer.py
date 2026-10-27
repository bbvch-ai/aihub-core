"""Live acceptance tests for the Presidio analyzer image and its recognizer config.

NOT part of a CI `make test` scope, like the other infra tests: they need the image and a running container.

    # against the dev stack (port 5002), from the repository root
    PRESIDIO_ANALYZER_URL=http://localhost:5002 PRESIDIO_ANALYZER_API_KEY=... \
        uv run pytest infra/deployment/docker/presidio-analyzer/ -v

    # the same language and key checks from inside a caller container (stdlib only, no pytest there)
    docker exec -i -e PRESIDIO_ANALYZER_URL=http://presidio-analyzer:3000 -e PRESIDIO_ANALYZER_API_KEY=... \
        litellm python - < infra/deployment/docker/presidio-analyzer/test_presidio_analyzer.py

The egress and request-timeout tests start their own container, so they need the docker CLI and the image tag pinned
in compose-config.yml. The concurrency tests analyse 20k-token texts side by side and take several minutes; they print
the latencies documented in infra/deployment/CLAUDE.md.
"""

import json
import os
import re
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

URL = os.environ.get("PRESIDIO_ANALYZER_URL", "http://localhost:5002").rstrip("/")
API_KEY = os.environ.get("PRESIDIO_ANALYZER_API_KEY", "")
ENTITIES = ["PERSON", "LOCATION", "CH_ADDRESS", "EMAIL_ADDRESS", "PHONE_NUMBER", "IBAN_CODE", "NATIONAL_ID", "CH_MRN",
            "CH_ID_DOCUMENT", "CH_INSURANCE_CARD", "DATE_OF_BIRTH"]
ADDRESS = {"CH_ADDRESS", "LOCATION"}

# One text per language, every one sent with the language code `de`; each value must be fully covered by a span of
# one of the listed types.
SAMPLES = {
    "de": ("Patient: Reto Wyss, geb. 14.03.1978, AHV-Nr. 756.1234.5678.97, wohnhaft Seefeldstrasse 18, 8008 Zürich. "
           "Tel. 044 270 41 87, E-Mail reto.wyss@example.ch. IBAN CH93 0076 2011 6238 5295 7. Fall-Nr. 2024-118234. "
           "Versichertenkarte 80756 01234 56789 01234. Pass-Nr. X1234567.",
           [({"PERSON"}, "Reto Wyss"), ({"DATE_OF_BIRTH"}, "14.03.1978"), ({"NATIONAL_ID"}, "756.1234.5678.97"),
            (ADDRESS, "Seefeldstrasse 18, 8008 Zürich"), ({"PHONE_NUMBER"}, "044 270 41 87"),
            ({"EMAIL_ADDRESS"}, "reto.wyss@example.ch"), ({"IBAN_CODE"}, "CH93 0076 2011 6238 5295 7"),
            ({"CH_MRN"}, "2024-118234"), ({"CH_INSURANCE_CARD"}, "80756 01234 56789 01234"),
            ({"CH_ID_DOCUMENT"}, "X1234567")]),
    "fr": ("Madame Sophie Martin, née le 02.05.1985, domiciliée Rue de Lausanne 12, 1201 Genève, tél. +41 22 345 67 89, "
           "numéro de sécurité sociale 2 85 05 75 123 456 78.",
           [({"PERSON"}, "Sophie Martin"), ({"DATE_OF_BIRTH"}, "02.05.1985"),
            (ADDRESS, "Rue de Lausanne 12, 1201 Genève"), ({"PHONE_NUMBER"}, "+41 22 345 67 89"),
            ({"NATIONAL_ID"}, "2 85 05 75 123 456 78")]),
    "it": ("Il signor Marco Rossi, nato il 12.07.1979, codice fiscale RSSMRC79L12H501M, residente in Via Roma 25, "
           "6900 Lugano, telefono 091 123 45 67, e-mail marco.rossi@example.it.",
           [({"PERSON"}, "Marco Rossi"), ({"DATE_OF_BIRTH"}, "12.07.1979"), ({"NATIONAL_ID"}, "RSSMRC79L12H501M"),
            (ADDRESS, "Via Roma 25, 6900 Lugano"), ({"PHONE_NUMBER"}, "091 123 45 67"),
            ({"EMAIL_ADDRESS"}, "marco.rossi@example.it")]),
    "en": ("Mr John Smith, date of birth 03/14/1985, Social Security Number 123-45-6789, National Insurance number "
           "AB 12 34 56 C, phone +44 20 7946 0958, email john.smith@example.com, IBAN GB82 WEST 1234 5698 7654 32.",
           [({"PERSON"}, "John Smith"), ({"DATE_OF_BIRTH"}, "03/14/1985"), ({"NATIONAL_ID"}, "123-45-6789"),
            ({"NATIONAL_ID"}, "AB 12 34 56 C"), ({"PHONE_NUMBER"}, "+44 20 7946 0958"),
            ({"EMAIL_ADDRESS"}, "john.smith@example.com"), ({"IBAN_CODE"}, "GB82 WEST 1234 5698 7654 32")]),
}

LONG_PROMPT_TOKENS = 20_000


def request(path: str, body: dict | None = None, api_key: str | None = API_KEY, timeout: float = 60,
            url: str = URL) -> tuple[int, object]:
    headers = {"Content-Type": "application/json"}
    if api_key is not None:
        headers["Authorization"] = f"Bearer {api_key}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{url}{path}", data=data, headers=headers, method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode()
            status = response.status
    except urllib.error.HTTPError as error:
        raw, status = error.read().decode(), error.code
    try:
        return status, json.loads(raw)
    except json.JSONDecodeError:
        return status, raw


def analyze(text: str, timeout: float = 60, url: str = URL, api_key: str = API_KEY) -> list[dict]:
    status, spans = request("/analyze", {"text": text, "language": "de", "entities": ENTITIES}, api_key=api_key,
                            timeout=timeout, url=url)
    assert status == 200, (status, spans)
    return spans


def missing_values(language: str) -> list[str]:
    """Expected values not fully covered by a span of an accepted type."""
    text, expected = SAMPLES[language]
    spans = analyze(text)
    missing = []
    for types, value in expected:
        start = text.index(value)
        end = start + len(value)
        if not any(s["entity_type"] in types and s["start"] <= start and s["end"] >= end for s in spans):
            missing.append(f"{sorted(types)} {value!r}")
    return missing


def check_language(language: str) -> None:
    missing = missing_values(language)
    assert not missing, f"{language}: not masked {missing}"


def check_health_without_key() -> None:
    status, body = request("/health", api_key=None)
    assert status == 200, (status, body)


def check_rejects_missing_key() -> None:
    status, body = request("/analyze", {"text": "Reto Wyss", "language": "de"}, api_key=None)
    assert status == 401, (status, body)


def check_rejects_wrong_key() -> None:
    status, body = request("/analyze", {"text": "Reto Wyss", "language": "de"}, api_key="wrong-key")
    assert status == 401, (status, body)


def test_should_mask_german_swiss_text_when_sent_as_de() -> None:
    check_language("de")


def test_should_mask_french_text_when_sent_as_de() -> None:
    check_language("fr")


def test_should_mask_italian_text_when_sent_as_de() -> None:
    check_language("it")


def test_should_mask_english_text_when_sent_as_de() -> None:
    check_language("en")


def test_should_answer_health_probe_when_no_key_is_sent() -> None:
    check_health_without_key()


def test_should_reject_analysis_when_api_key_is_missing() -> None:
    check_rejects_missing_key()


def test_should_reject_analysis_when_api_key_is_wrong() -> None:
    check_rejects_wrong_key()


# GLiNER reads the text in chunks of about 250 characters; in this prompt the second chunk would start inside "Nenne".
CHUNKED_PROMPT = ("Sie sind ein Assistent und antworten dem Benutzer in seiner Sprache. Schreibe Ihnen eine Mahnung an "
                  "Anna Muster, AHV-Nr. 756.9876.5432.10, Bahnhofstrasse 5, 3011 Bern, IBAN CH93 0076 2011 6238 5295 "
                  "7. Nenne darin Name, AHV-Nummer, Adresse, Identität und IBAN.")


def word_fragments(text: str, spans: list[dict]) -> list[str]:
    def inside_word(position: int) -> bool:
        return 0 < position < len(text) and text[position - 1].isalnum() and text[position].isalnum()

    return [text[s["start"]:s["end"]] for s in spans if inside_word(s["start"]) or inside_word(s["end"])]


def test_should_detect_no_word_fragment_when_text_spans_several_model_chunks() -> None:
    fragments = word_fragments(CHUNKED_PROMPT, analyze(CHUNKED_PROMPT))

    assert len(CHUNKED_PROMPT) > 250
    assert not fragments, fragments


def test_should_still_detect_a_name_cut_by_a_model_chunk_end() -> None:
    lead = "Bitte prüfen Sie den folgenden Fall sorgfältig und melden Sie sich bei Fragen. " * 3
    text = f"{lead}Die Mahnung geht an Anna Muster in Bern."

    spans = analyze(text)

    start = text.index("Anna Muster")
    assert any(s["entity_type"] == "PERSON" and s["start"] <= start and s["end"] >= start + len("Anna Muster")
               for s in spans), spans


def test_should_end_postcode_and_city_at_the_sentence_end() -> None:
    text = "Anna Muster wohnt an der Bahnhofstrasse 5, 3011 Bern. Nenne ihre Adresse. Reto Wyss wohnt in 9000 St. Gallen."

    covered = {text[s["start"]:s["end"]] for s in analyze(text) if s["entity_type"] in ADDRESS}

    assert "3011 Bern" in covered
    assert not [value for value in covered if "Nenne" in value]
    assert [value for value in covered if "9000 St. Gallen" in value]


def uncovered(text: str, entity_type: str, values: list[str]) -> list[str]:
    """Every occurrence of each value not fully covered by a span of the type."""
    spans = [s for s in analyze(text) if s["entity_type"] == entity_type]
    return [f"{value}@{match.start()}" for value in values for match in re.finditer(re.escape(value), text)
            if not any(s["start"] <= match.start() and s["end"] >= match.end() for s in spans)]


def test_should_detect_a_single_surname_after_a_form_label() -> None:
    text = "Nachname: Brunner\nVorname: Lea\nNom: Rochat\nCognome: Bernasconi\nLast name: Keller"

    assert not uncovered(text, "PERSON", ["Brunner", "Lea", "Rochat", "Bernasconi", "Keller"])


# In a mail thread full of names GLiNER drops a lone surname after a title; this is the thread where it did.
NAME_HEAVY_THREAD = (
    "Von: Martina Tschudi <martina.tschudi@spital-seeland.ch>\nGesendet: 24. Oktober 2026\nAn: Andrea Tschudi\n"
    "Betreff: AW: SR-20241015-0042\n\nTelefonnotiz 08.02.2026: Herr Tschudi ruft an wegen der Rechnung "
    "2024-28238 über Fr. 85.–. Er bittet um Rückruf auf +41 (0)76 746 18 90. Adresse im System prüfen: "
    "General-Guisan-Strasse 60b, 9000 St. Gallen.\n\n--------------------\nVon: Andrea Tschudi "
    "<a.tschudi@sunrise.ch>\nGesendet: 20. Juli 2023\nAn: Martina Tschudi\nBetreff: AW: SR-20241015-0042\n\n"
    "Spitex-Bericht: Frau Tschudi (Morbus Parkinson) ist stabil. Note téléphonique du 10.02.2025 : M. Jaquet "
    "appelle. Reminder: your appointment with Dr Gay-Crosier is on 20.11.")


def test_should_detect_a_surname_after_a_title() -> None:
    assert not uncovered(NAME_HEAVY_THREAD, "PERSON", ["Tschudi", "Jaquet", "Gay-Crosier"])


def test_should_detect_a_surname_after_patient_in_a_name_heavy_thread() -> None:
    # "Patient" is no title pattern, so this relies on GLiNER alone where it drops lone surnames after titles.
    text = f"{NAME_HEAVY_THREAD}\n\nVisite 21.11.: Patient Tschudi klagt über Schwindel. The patient Jaquet was discharged."

    assert not uncovered(text, "PERSON", ["Tschudi", "Jaquet"])


def test_should_detect_a_case_number_after_a_label_and_a_connector_word() -> None:
    text = ("PID isch 5495489. The case number is 4471128. Numéro de séjour 77120934. Numero di caso 3381204. "
            "Fallnummer ist 2209183.")

    assert not uncovered(text, "CH_MRN", ["5495489", "4471128", "77120934", "3381204", "2209183"])


def masked(text: str, entity_type: str) -> list[str]:
    return [text[s["start"]:s["end"]] for s in analyze(text) if s["entity_type"] == entity_type]


def test_should_not_take_a_value_after_a_non_person_name_label_for_a_name() -> None:
    text = "Company name: Swisscom\nProject name: Phoenix\nFile name: Report.pdf"

    assert not masked(text, "PERSON")


def test_should_not_take_a_title_or_a_heading_word_after_a_title_for_a_name() -> None:
    text = "Frau Dr. Meier. Herr Prof. Dr. Müller. Patient Information. Patient Summary. Seen the patient Monday."

    spans = masked(text, "PERSON")

    assert not uncovered(text, "PERSON", ["Meier", "Müller"])
    assert not [s for s in spans if s.rstrip(".") in {"Dr", "Prof"} or {"Information", "Summary", "Monday"} & set(s.split())]


def test_should_detect_a_case_number_after_patient_nr() -> None:
    text = "Patient Nr. 4471128. Patient-Nr. 5495489."

    assert not masked(text, "PERSON")
    assert not uncovered(text, "CH_MRN", ["4471128", "5495489"])


def test_should_not_take_an_invoice_number_for_an_insurance_card() -> None:
    text = "Rechnung Nr. 9434765919 vom 3. März, zahlbar innert 30 Tagen."

    assert not [s for s in analyze(text) if s["entity_type"] == "CH_INSURANCE_CARD"]


def long_prompt() -> str:
    """A mail thread of about LONG_PROMPT_TOKENS tokens (cl100k), with personal data in every message."""
    import tiktoken

    encoding = tiktoken.get_encoding("cl100k_base")
    parts, tokens, index = [], 0, 0
    while tokens < LONG_PROMPT_TOKENS:
        language = list(SAMPLES)[index % len(SAMPLES)]
        part = (f"Von: Kundendienst <service@example.ch>\nBetreff: Anfrage {index}\n\n{SAMPLES[language][0]} "
                "Wir bitten Sie, die beiliegenden Unterlagen bis Ende Monat zu prüfen und uns Rückmeldung zu geben. "
                "Bei Fragen stehen wir Ihnen gerne zur Verfügung.\n\n")
        parts.append(part)
        tokens += len(encoding.encode(part))
        index += 1
    return "".join(parts)


def test_should_report_latency_when_prompt_has_20k_tokens() -> None:
    import tiktoken

    text = long_prompt()
    tokens = len(tiktoken.get_encoding("cl100k_base").encode(text))
    started = time.perf_counter()
    spans = analyze(text, timeout=600)
    seconds = time.perf_counter() - started
    print(f"\nLONG PROMPT: {tokens} tokens, {len(text)} characters, {len(spans)} spans, {seconds:.1f} s")
    assert tokens >= LONG_PROMPT_TOKENS
    assert spans


# What the gateway guardrail and the Docker healthcheck can live with while long texts are analysed. The compose
# healthcheck gives the probe 6 s; the idle figure is the single-request latency measured before the threaded worker.
SHORT_REQUEST_UNDER_LOAD_SECONDS = 1.0
SHORT_REQUEST_IDLE_SECONDS = 0.3
HEALTH_PROBE_SECONDS = 5
SHORT_TEXT = SAMPLES["de"][0]


def seconds(call: Callable[[], object]) -> float:
    started = time.perf_counter()
    call()
    return time.perf_counter() - started


def while_analysing(texts: list[str], probe: Callable[[], object], url: str = URL,
                    api_key: str = API_KEY) -> tuple[list[float], list[list[dict]]]:
    """Times the probe once a second for as long as the texts are analysed in parallel, then returns their spans."""
    with ThreadPoolExecutor(len(texts)) as pool:
        running = [pool.submit(analyze, text, 900, url, api_key) for text in texts]
        time.sleep(3)
        timings = []
        while not all(analysis.done() for analysis in running):
            timings.append(seconds(probe))
            time.sleep(1)
        results = [analysis.result() for analysis in running]
    assert timings, "the long analyses finished before the first probe"
    return timings, results


def report(name: str, timings: list[float]) -> None:
    print(f"\n{name}: {len(timings)} probes, median {statistics.median(timings):.2f} s, max {max(timings):.2f} s")


def test_should_answer_a_short_request_within_a_second_while_a_20k_token_text_is_analysed() -> None:
    timings, _ = while_analysing([long_prompt()], lambda: analyze(SHORT_TEXT))

    report("SHORT REQUEST BESIDE ONE LONG ANALYSIS", timings)
    assert max(timings) < SHORT_REQUEST_UNDER_LOAD_SECONDS, timings


def test_should_answer_the_health_probe_while_long_analyses_run() -> None:
    def probe() -> None:
        status, body = request("/health", api_key=None, timeout=HEALTH_PROBE_SECONDS)
        assert status == 200, (status, body)

    timings, _ = while_analysing([long_prompt()] * 3, probe)

    report("HEALTH PROBE BESIDE THREE LONG ANALYSES", timings)


def test_should_answer_a_short_request_on_an_idle_analyzer_as_fast_as_before() -> None:
    analyze(SHORT_TEXT)
    timings = [seconds(lambda: analyze(SHORT_TEXT)) for _ in range(10)]

    report("SHORT REQUEST ON AN IDLE ANALYZER", timings)
    assert statistics.median(timings) < SHORT_REQUEST_IDLE_SECONDS, timings


def comparable(spans: list[dict]) -> list[tuple]:
    return sorted((s["start"], s["end"], s["entity_type"], round(s["score"], 4)) for s in spans)


def test_should_detect_the_same_spans_under_concurrent_load_as_one_at_a_time() -> None:
    texts = [text for text, _ in SAMPLES.values()] + [CHUNKED_PROMPT, NAME_HEAVY_THREAD]
    one_at_a_time = [comparable(analyze(text)) for text in texts]

    with ThreadPoolExecutor(len(texts) + 1) as pool:
        pool.submit(analyze, long_prompt(), 900)
        concurrent = [comparable(spans) for spans in pool.map(analyze, texts * 3)]

    assert concurrent == one_at_a_time * 3


def compose_image() -> str:
    tag = re.search(r"^  presidio_analyzer: (\S+)$", (repo_root() / "infra/deployment/compose-config.yml")
                    .read_text(encoding="utf-8"), re.M)
    assert tag, "image_tags.presidio_analyzer not found"
    return f"ghcr.io/bbvch-ai/aihub-core/{tag.group(1)}"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def test_should_pin_the_built_image_in_every_compose_file() -> None:
    image = compose_image()
    for compose in sorted((repo_root() / "infra").glob("docker-compose.*.yml")):
        assert f"image: {image}\n" in compose.read_text(encoding="utf-8"), compose.name
    workflow = (repo_root() / ".github/workflows/build-presidio-analyzer.yml").read_text(encoding="utf-8")
    assert ".image_tags.presidio_analyzer" in workflow
    assert "context: infra/deployment/docker/presidio-analyzer" in workflow


def docker(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *args], capture_output=True, text=True, check=check)


def in_container(container: str, code: str) -> subprocess.CompletedProcess:
    return docker("exec", container, "python", "-c", code, check=False)


def start_analyzer(container: str, key: str, *options: str) -> None:
    """Runs the pinned image as `container` with the repository's recognizer config and waits for its models."""
    config = repo_root() / "infra/configs/presidio/analyzer.yaml"
    docker("rm", "-f", container, check=False)
    docker("run", "-d", "--name", container, "-e", f"ANALYZER_API_KEY={key}", "-v", f"{config}:/app/analyzer.yaml:ro",
           *options, compose_image())
    health = "import urllib.request; print(urllib.request.urlopen('http://localhost:3000/health', timeout=5).read())"
    deadline = time.time() + 300
    while in_container(container, health).returncode != 0:
        assert time.time() < deadline, docker("logs", container, check=False).stdout[-2000:]
        time.sleep(5)


def test_should_keep_serving_other_callers_when_an_analysis_outlives_the_request_timeout() -> None:
    """The timeout is lowered below one analysis but above the model load, which it also bounds."""
    container, key, timeout = "presidio-analyzer-timeout-test", "timeout-test-key", 60
    try:
        start_analyzer(container, key, "-p", "127.0.0.1::3000", "--cpus", "4", "--memory", "4g",
                       "-e", f"GUNICORN_TIMEOUT={timeout}")
        url = f"http://{docker('port', container, '3000').stdout.splitlines()[0]}"
        started = time.perf_counter()

        timings, [spans] = while_analysing([long_prompt() * 2], lambda: analyze(SHORT_TEXT, url=url, api_key=key),
                                           url=url, api_key=key)

        took = time.perf_counter() - started
        logs = docker("logs", container, check=False)
        report(f"SHORT REQUEST BESIDE A {took:.0f} S ANALYSIS (TIMEOUT {timeout} S)", timings)
        assert took > timeout
        assert spans
        assert "WORKER TIMEOUT" not in logs.stdout + logs.stderr
        assert analyze(SHORT_TEXT, url=url, api_key=key)
    finally:
        docker("rm", "-f", container, check=False)


def test_should_start_and_answer_when_egress_is_blocked() -> None:
    """The analyzer runs on an internal network (no route out) and still loads its models and answers."""
    network, container, key = "pii-egress-test", "presidio-analyzer-egress-test", "egress-test-key"
    docker("rm", "-f", container, check=False)
    docker("network", "rm", network, check=False)
    docker("network", "create", "--internal", network)
    try:
        start_analyzer(container, key, "--network", network)
        post =("import json, urllib.request; r = urllib.request.Request('http://localhost:3000/analyze', "
                "data=json.dumps({'text': 'Patient Reto Wyss, AHV 756.1234.5678.97', 'language': 'de'}).encode(), "
                f"headers={{'Content-Type': 'application/json', 'Authorization': 'Bearer {key}'}}); "
                "print(sorted({s['entity_type'] for s in json.load(urllib.request.urlopen(r, timeout=60))}))")
        answer = in_container(container, post)
        print(f"\nOFFLINE ANALYZE: {answer.stdout.strip()}")
        assert "PERSON" in answer.stdout and "NATIONAL_ID" in answer.stdout, answer.stderr
        outbound = in_container(container, "import urllib.request; urllib.request.urlopen('https://huggingface.co', "
                                           "timeout=10)")
        print(f"OUTBOUND ATTEMPT: exit {outbound.returncode}, {outbound.stderr.strip().splitlines()[-1]}")
        assert outbound.returncode != 0
    finally:
        docker("rm", "-f", container, check=False)
        docker("network", "rm", network, check=False)


if __name__ == "__main__":
    checks = [("health without key", check_health_without_key), ("missing key rejected", check_rejects_missing_key),
              ("wrong key rejected", check_rejects_wrong_key)]
    checks += [(f"{language} masked", lambda language=language: check_language(language)) for language in SAMPLES]
    failed = 0
    for name, check in checks:
        try:
            check()
            print(f"PASS {name}")
        except AssertionError as error:
            failed += 1
            print(f"FAIL {name}: {error}")
    print(f"{len(checks) - failed}/{len(checks)} passed against {URL}")
    sys.exit(1 if failed else 0)
