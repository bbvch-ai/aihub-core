from swiss_ai_hub.core.generative_ai.anonymisation.placeholder_map import PlaceholderMap
from swiss_ai_hub.core.infrastructure.presidio_analyzer.analyzer_span import AnalyzerSpan


def span_of(text: str, value: str, entity_type: str, occurrence: int = 0) -> AnalyzerSpan:
    start = -1
    for _ in range(occurrence + 1):
        start = text.index(value, start + 1)
    return AnalyzerSpan(entity_type=entity_type, start=start, end=start + len(value))


def test_should_replace_every_detected_entity_when_masking() -> None:
    text = "Anna Muster, anna@example.ch, IBAN CH93 0076 2011 6238 5295 7"
    spans = [
        span_of(text, "Anna Muster", "PERSON"),
        span_of(text, "anna@example.ch", "EMAIL_ADDRESS"),
        span_of(text, "CH93 0076 2011 6238 5295 7", "IBAN_CODE"),
    ]

    masked = PlaceholderMap().mask(text, spans)

    assert masked == "<PERSON_1>, <EMAIL_ADDRESS_2>, IBAN <IBAN_CODE_3>"


def test_should_give_one_value_one_placeholder_when_it_repeats() -> None:
    text = "Anna Muster schreibt. Gruss, Anna Muster"
    spans = [span_of(text, "Anna Muster", "PERSON"), span_of(text, "Anna Muster", "PERSON", occurrence=1)]

    masked = PlaceholderMap().mask(text, spans)

    assert masked == "<PERSON_1> schreibt. Gruss, <PERSON_1>"


def test_should_keep_a_placeholder_across_messages_when_the_value_returns() -> None:
    placeholders = PlaceholderMap()
    first = "Termin mit Anna Muster"
    placeholders.mask(first, [span_of(first, "Anna Muster", "PERSON")])
    second = "Peter Meier und Anna Muster"

    masked = placeholders.mask(
        second, [span_of(second, "Peter Meier", "PERSON"), span_of(second, "Anna Muster", "PERSON")]
    )

    assert masked == "<PERSON_2> und <PERSON_1>"


def test_should_merge_overlapping_detections_into_the_longest_type() -> None:
    text = "wohnt an der Bahnhofstrasse 1, 8001 Zürich."
    address = "Bahnhofstrasse 1, 8001 Zürich"
    spans = [span_of(text, address, "CH_ADDRESS"), span_of(text, "Zürich", "LOCATION")]

    masked = PlaceholderMap().mask(text, spans)

    assert masked == "wohnt an der <CH_ADDRESS_1>."


def test_should_leave_placeholders_already_in_the_text_and_skip_their_numbers() -> None:
    text = "<PERSON_1> trifft Anna Muster"
    spans = [AnalyzerSpan(entity_type="PERSON", start=0, end=10), span_of(text, "Anna Muster", "PERSON")]

    masked = PlaceholderMap().mask(text, spans)

    assert masked == "<PERSON_1> trifft <PERSON_2>"


def test_should_restore_a_placeholder_repeated_several_times() -> None:
    placeholders = PlaceholderMap(values={"<PERSON_1>": "Anna Muster", "<LOCATION_2>": "Bern"})

    restored = placeholders.restore("<PERSON_1> zieht nach <LOCATION_2>. <PERSON_1> freut sich, <PERSON_1>!")

    assert restored == "Anna Muster zieht nach Bern. Anna Muster freut sich, Anna Muster!"


def test_should_leave_placeholders_it_never_issued_when_restoring() -> None:
    placeholders = PlaceholderMap(values={"<PERSON_1>": "Anna Muster"})

    restored = placeholders.restore("<PERSON_1> und <PERSON_7>")

    assert restored == "Anna Muster und <PERSON_7>"


def test_should_list_unknown_placeholders_once_each() -> None:
    placeholders = PlaceholderMap(values={"<PERSON_1>": "Anna Muster"})

    assert placeholders.unknown_in("<PERSON_1>, <PERSON_7>, <EMAIL_ADDRESS_9>, <PERSON_7>") == [
        "<PERSON_7>",
        "<EMAIL_ADDRESS_9>",
    ]


def test_should_tell_a_text_to_restore_only_by_its_own_placeholders() -> None:
    placeholders = PlaceholderMap(values={"<PERSON_1>": "Anna Muster"})

    assert placeholders.issued_in("Bitte <PERSON_1> anrufen")
    assert not placeholders.issued_in("Bitte <PERSON_2> anrufen")
    assert not placeholders.issued_in("Zeile<br>Umbruch <person_1>")


def test_should_survive_a_round_trip_through_json() -> None:
    placeholders = PlaceholderMap()
    text = "Anna Muster"
    placeholders.mask(text, [span_of(text, "Anna Muster", "PERSON")])

    reloaded = PlaceholderMap.model_validate(placeholders.model_dump())

    assert reloaded.mask("Peter", [AnalyzerSpan(entity_type="PERSON", start=0, end=5)]) == "<PERSON_2>"
    assert reloaded.restore("<PERSON_1>") == "Anna Muster"
