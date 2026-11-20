from datetime import date

import pytest

from swiss_ai_hub.core.generative_ai.document.classification.date_precision import DatePrecision
from swiss_ai_hub.core.generative_ai.document.classification.period_text_parser import PeriodTextParser

pytestmark = pytest.mark.unit

_FEBRUARY = (date(2025, 2, 1), date(2025, 2, 28))


@pytest.mark.parametrize(
    "raw",
    [
        "01.02.2025 - 28.02.2025",
        "01.02.2025 – 28.02.2025",
        "01.02.2025 bis 28.02.2025",
        "Leistungszeitraum: 01.02.2025 - 28.02.2025",
        "1.2.–28.2.2025",
        "1.–28.2.2025",
        "du 1er au 28 février 2025",
        "dal 1 al 28 febbraio 2025",
        "2025-02-01 to 2025-02-28",
    ],
)
def test_a_range_of_days_is_read_in_every_form(raw: str) -> None:
    parsed = PeriodTextParser.parse(raw)

    assert parsed is not None
    assert (parsed.start, parsed.end) == _FEBRUARY
    assert parsed.precision == DatePrecision.DAY


def test_a_month_stands_for_the_whole_month() -> None:
    parsed = PeriodTextParser.parse("Februar 2025")

    assert parsed is not None
    assert (parsed.start, parsed.end, parsed.precision) == (*_FEBRUARY, DatePrecision.MONTH)


def test_a_single_date_of_supply_is_a_one_day_period() -> None:
    parsed = PeriodTextParser.parse("Lieferdatum 14.03.2025")

    assert parsed is not None
    assert parsed.start == parsed.end == date(2025, 3, 14)


@pytest.mark.parametrize("raw", ["28.02.2025 - 01.02.2025", "laufend", None])
def test_a_reversed_range_or_no_date_is_no_period(raw: str | None) -> None:
    assert PeriodTextParser.parse(raw) is None


_FIRST_QUARTER = (date(2025, 1, 1), date(2025, 3, 31))


@pytest.mark.parametrize(
    "raw",
    [
        "1. Januar bis 31. März 2025",
        "1er janvier au 31 mars 2025",
        "dal 1 gennaio al 31 marzo 2025",
        "1 January – 31 March 2025",
        "January 1 – March 31, 2025",
        "1.1.–31.3.2025",
    ],
)
def test_a_range_whose_start_leaves_out_the_year_takes_it_from_the_end(raw: str) -> None:
    parsed = PeriodTextParser.parse(raw)

    assert parsed is not None
    assert (parsed.start, parsed.end, parsed.precision) == (*_FIRST_QUARTER, DatePrecision.DAY)


@pytest.mark.parametrize(
    "raw",
    [
        "Januar – März 2025",
        "Januar bis März 2025",
        "de janvier à mars 2025",
        "da gennaio a marzo 2025",
        "January – March 2025",
        "01.2025 – 03.2025",
    ],
)
def test_a_range_of_months_covers_every_month_at_month_precision(raw: str) -> None:
    parsed = PeriodTextParser.parse(raw)

    assert parsed is not None
    assert (parsed.start, parsed.end, parsed.precision) == (*_FIRST_QUARTER, DatePrecision.MONTH)


def test_a_range_of_months_may_cross_the_year() -> None:
    parsed = PeriodTextParser.parse("Dezember 2024 – Februar 2025")

    assert parsed is not None
    assert (parsed.start, parsed.end) == (date(2024, 12, 1), date(2025, 2, 28))


@pytest.mark.parametrize(
    "raw",
    ["Januar bis 31.03.2025", "März – Januar 2025", "Leistung 1. Februar 2025, Rechnung März 2025"],
)
def test_two_dates_in_no_form_read_here_store_no_period_rather_than_one_end(raw: str) -> None:
    assert PeriodTextParser.parse(raw) is None


@pytest.mark.parametrize("raw", ["1. Mai 2025", "14 March 2025"])
def test_one_date_written_with_its_month_name_is_still_one_date(raw: str) -> None:
    parsed = PeriodTextParser.parse(raw)

    assert parsed is not None
    assert parsed.start == parsed.end


@pytest.mark.parametrize(
    ("raw", "ends"),
    [
        ("01.02.2025 bis 28.02.2025", (True, True)),
        ("Februar 2025", (True, True)),
        ("14.03.2025", (True, True)),
        ("Das Mietverhältnis beginnt am 1. Juli 2025 und läuft auf unbestimmte Zeit", (True, False)),
        ("ab 1. April 2025", (True, False)),
        ("Dieser Nachtrag tritt am 1. März 2026 in Kraft", (True, False)),
        ("L'accord prend effet le 1er décembre 2025 et est conclu pour une durée de 24 mois", (True, False)),
        ("Laufzeit 24 Monate ab 1. Dezember 2025", (True, False)),
        ("The services commence on 1 February 2026 and continue until they are completed", (True, False)),
        ("from 1 April 2025 until terminated", (True, False)),
        ("in vigore dal 1° maggio 2025", (True, False)),
        ("Das Mietverhältnis endet ohne Kündigung am 30. Juni 2027", (False, True)),
        ("Vertrag läuft bis 31.12.2026, Beginn mit Unterzeichnung", (False, True)),
        ("valable jusqu'au 31 mars 2026", (False, True)),
    ],
)
def test_a_word_next_to_a_single_date_says_which_end_of_the_period_it_is(raw: str, ends: tuple[bool, bool]) -> None:
    assert PeriodTextParser.stated_ends(raw) == ends


@pytest.mark.parametrize(
    ("raw", "line", "ends"),
    [
        (
            "le 1er décembre 2025",
            "L'accord prend effet le 1er décembre 2025 et est conclu pour 24 mois.",
            (True, False),
        ),
        ("1. April 2025", "Stellenantritt: 1. April 2025", (True, False)),
        ("30. Juni 2027", "Das Mietverhältnis endet ohne Kündigung am 30. Juni 2027.", (False, True)),
        ("14.03.2025", "Lieferdatum: 14.03.2025 · zahlbar bis 13.04.2025", (True, True)),
        ("1. April 2025", "Vertragsbeginn: 1. April 2025", (True, False)),
        ("1. Juli 2025", "Mietbeginn: 1. Juli 2025", (True, False)),
        ("1. Mai 2025", "Dienstantritt am 1. Mai 2025", (True, False)),
        ("31. März 2027", "Mietende: 31. März 2027", (False, True)),
        ("31.12.2026", "Laufzeitende 31.12.2026", (False, True)),
        ("30.06.2026", "Vertragsablauf: 30.06.2026", (False, True)),
        ("1. Januar 2025", "in der geltende Fassung vom 1. Januar 2025", (True, True)),
        ("März 2025", "Lieferung bis spätestens Ende Monat. Leistungszeitraum: März 2025", (True, True)),
        ("31.12.2026", "Gültig bis inkl. 31.12.2026", (False, True)),
        ("30. Juni 2027", "Das Mietverhältnis endet am **30. Juni** 2027.", (False, True)),
        ("1. Juli 2025", "Mietbeginn: __1. Juli__ 2025", (True, False)),
    ],
)
def test_a_date_copied_without_its_word_is_read_in_the_line_it_came_from(
    raw: str, line: str, ends: tuple[bool, bool]
) -> None:
    assert PeriodTextParser.stated_ends(raw, context=line) == ends
