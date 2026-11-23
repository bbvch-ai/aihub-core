import pytest

from swiss_ai_hub.core.generative_ai.document.loaders.mineru_inline_latex import MineruInlineLatex

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("latex", "text"),
    [
        (r"Etat: $1^{\text{er}}$ janvier 2003", "Etat: 1er janvier 2003"),
        (r"$1^{\mathrm{er}}$ avril", "1er avril"),
        (r"dal $1^{\circ}$ maggio 2024", "dal 1° maggio 2024"),
        (r"la $13^{\text{ème}}$ rente", "la 13ème rente"),
        (r"Art. $52^{\mathrm{bis}}$ AHVG", "Art. 52bis AHVG"),
        (r"Art. $33^{\text{ter}}$ AHVV", "Art. 33ter AHVV"),
        (r"$\mathrm{CO}_{2}$-Ausstoss", "CO2-Ausstoss"),
        (r"$50\%$ der Prämie", "50% der Prämie"),
        (r"$1.1^{\circ}C$ wärmer", "1.1°C wärmer"),
        (r"Sie $\text{dürfen}$ nicht", "Sie dürfen nicht"),
        (r"Zahlung $\rightarrow$ Konto", "Zahlung → Konto"),
        (r"$n^0$ 12 et $n^{\mathrm{os}}$ 3", "n° 12 et nos 3"),
    ],
)
def test_text_written_as_inline_latex_is_read_as_that_text(latex: str, text: str) -> None:
    assert MineruInlineLatex.as_text(latex) == text


@pytest.mark.parametrize(
    ("latex", "text"),
    [
        (r"siehe Urteil$^{1}$", "siehe Urteil¹"),
        (r"10$^{6}$ Franken", "10⁶ Franken"),
        (r"120 m$^{2}$", "120 m²"),
        (r"10$^{-3}$", "10⁻³"),
    ],
)
def test_a_superscript_number_stays_a_superscript(latex: str, text: str) -> None:
    assert MineruInlineLatex.as_text(latex) == text


@pytest.mark.parametrize(
    "formula",
    [
        r"$a^2 + b^2 = c^2$",
        r"$\sqrt{(b^2 - 4ac)}$",
        r"$\sum x \to \infty$",
        r"$D_{x}$",
        r"$B_{5}(y)$",
        r"$58^{4/12} - 60$",
        r"$\pi \approx 3.14$",
    ],
)
def test_a_formula_keeps_its_latex(formula: str) -> None:
    assert MineruInlineLatex.as_text(f"Es gilt {formula}.") == f"Es gilt {formula}."


@pytest.mark.parametrize(
    "text",
    ["Total $ 9.35 and $ 12 net", "Total: $9.35 and $12.00 net", "a cost of $50 and a fee of $5", "no dollars at all"],
)
def test_dollar_amounts_in_running_text_are_left_alone(text: str) -> None:
    assert MineruInlineLatex.as_text(text) == text


@pytest.mark.parametrize(
    ("text", "comparable"),
    [
        (r"Urteil$^{1}$ des", "Urteil ¹ des"),
        ("Muster AG² und", "Muster AG ² und"),
        (r"am 1. Januar 2003$^{12}$", "am 1. Januar 2003 ¹²"),
        ("120 m²", "120 m ²"),
        ("Fussnote ¹ steht frei", "Fussnote ¹ steht frei"),
    ],
)
def test_for_comparison_a_superscript_number_is_set_apart_from_what_it_follows(text: str, comparable: str) -> None:
    assert MineruInlineLatex.as_comparable_text(text) == comparable
