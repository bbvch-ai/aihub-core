"""Regenerates the binary fixtures and ground_truth.json of the Universal Agent e2e specs.

Run from e2e/: uv run --no-project --with openpyxl --with reportlab python tests/universal-agent/fixtures/generate_fixtures.py
The output is deterministic, so regenerating without changing this script leaves git clean apart from xlsx zip
timestamps.
"""

import datetime
import json
from pathlib import Path

from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas

HERE = Path(__file__).parent
REGIONS = ["North", "South", "East", "West"]
QUARTERS = ["Q1", "Q2", "Q3", "Q4"]
PRODUCTS = ["Falcon", "Heron", "Otter"]
FIXED_TIME = datetime.datetime(2026, 1, 1)


def revenue(region_index: int, quarter_index: int, product_index: int) -> int:
    return 10_000 + 3_137 * region_index + 1_291 * quarter_index + 2_459 * product_index + 17 * (
        region_index * quarter_index + product_index
    )


def write_sales() -> dict:
    workbook = Workbook()
    workbook.properties.created = FIXED_TIME
    workbook.properties.modified = FIXED_TIME
    sheet = workbook.active
    sheet.title = "Sales"
    sheet.append(["Region", "Quarter", "Product", "Revenue (CHF)"])
    totals: dict[str, dict[str, int]] = {quarter: {region: 0 for region in REGIONS} for quarter in QUARTERS}
    for r, region in enumerate(REGIONS):
        for q, quarter in enumerate(QUARTERS):
            for p, product in enumerate(PRODUCTS):
                value = revenue(r, q, p)
                totals[quarter][region] += value
                sheet.append([region, quarter, product, value])
    workbook.save(HERE / "sales.xlsx")
    return {
        "q3_revenue_by_region": totals["Q3"],
        "lookup": {"region": "South", "quarter": "Q2", "product": "Heron", "revenue": revenue(1, 1, 1)},
    }


def write_pdf(name: str, lines: list[str]) -> None:
    canvas = Canvas(str(HERE / name), pagesize=A4, invariant=1)
    text = canvas.beginText(72, 770)
    for line in lines:
        text.textLine(line)
    canvas.drawText(text)
    canvas.save()


def write_broken_pdf() -> None:
    """A PDF header followed by a cut-off object and no xref: every parser rejects it."""
    (HERE / "broken.pdf").write_bytes(b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R\nstream\n\x00\x9c\xff\xfe")


def main() -> None:
    sales = write_sales()
    write_pdf(
        "alpha.pdf",
        [
            "Project Alpha briefing",
            "The code name of Project Alpha is AMBER-FALCON-42.",
            "Project Alpha is led by Dana Keller from the Basel office.",
        ],
    )
    write_pdf(
        "bravo.pdf",
        [
            "Project Bravo briefing",
            "The code name of Project Bravo is COBALT-OTTER-17.",
            "Project Bravo is led by Luca Brunner from the Lugano office.",
        ],
    )
    write_broken_pdf()
    ground_truth = {
        "sales.xlsx": sales,
        "alpha.pdf": {"code_name": "AMBER-FALCON-42", "lead": "Dana Keller"},
        "bravo.pdf": {"code_name": "COBALT-OTTER-17", "lead": "Luca Brunner"},
        "broken.pdf": {},
    }
    (HERE / "ground_truth.json").write_text(json.dumps(ground_truth, indent=2) + "\n")


if __name__ == "__main__":
    main()
