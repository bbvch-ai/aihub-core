"""Measures invoice classification against a real model through the dev stack's LiteLLM gateway (#2481).

Runs as ingestion will: the deployment's default text model (`DOCUMENT_INGESTION_LLM_MODEL`, override with
`DOCUMENT_CLASSIFICATION_TEST_MODEL`) at a deterministic temperature, through LiteLLM, whose PII guardrail anonymises
every call to a model not hosted locally. Running it with the guardrail on matters: #2312 saw company names masked as
`<PERSON_n>`, and issuer and recipient survive only if the model copies the placeholders exactly.

- The committed synthetic sample always runs.
- The real invoices run when `DOCUMENT_CLASSIFICATION_CORPUS` names their label file (see `ClassificationCorpus`).
- `DOCUMENT_CLASSIFICATION_REPORT_DIR` writes each report as markdown for the PR; `-s` prints it. The real
  documents' report names no case: their filenames, parties and amounts are confidential.
- `DOCUMENT_CLASSIFICATION_TEST_CONCURRENCY` sets how many calls run side by side (default 4).
"""

import os
from pathlib import Path

import pytest

from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.classification_case import (
    ClassificationCase,
)
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.classification_corpus import (
    ClassificationCorpus,
)
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.classification_evaluation import (
    ClassificationEvaluation,
)
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.classification_report import (
    ClassificationReport,
)
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.classification_report_markdown import (
    ClassificationReportMarkdown,
)
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig

pytestmark = pytest.mark.integration

_MODEL = os.environ.get("DOCUMENT_CLASSIFICATION_TEST_MODEL") or os.environ.get(
    "DOCUMENT_INGESTION_LLM_MODEL", "text-generation/gemma-4-31B-it"
)
_CONCURRENCY = int(os.environ.get("DOCUMENT_CLASSIFICATION_TEST_CONCURRENCY", "4"))
_CORPUS = os.environ.get("DOCUMENT_CLASSIFICATION_CORPUS")
_REPORT_DIR = os.environ.get("DOCUMENT_CLASSIFICATION_REPORT_DIR")


async def _report(name: str, cases: list[ClassificationCase], *, with_cases: bool) -> ClassificationReport:
    llm, cost_tracker = LLMConfig.deterministic(_MODEL).to_llama_index()
    results = await ClassificationEvaluation.run(cases, llm, _CONCURRENCY)
    costs = cost_tracker.get_total_costs()
    report = ClassificationReport(
        name=name,
        model=_MODEL,
        results=results,
        prompt_tokens=costs.prompt_token_count,
        completion_tokens=costs.completion_token_count,
    )
    markdown = ClassificationReportMarkdown.render(report, with_cases=with_cases)
    print(f"\n{markdown}\n")
    if _REPORT_DIR:
        Path(_REPORT_DIR).mkdir(parents=True, exist_ok=True)
        (Path(_REPORT_DIR) / f"{name.lower().replace(' ', '_')}.md").write_text(markdown, encoding="utf-8")
    return report


@pytest.mark.asyncio
async def test_the_synthetic_sample_meets_the_targets() -> None:
    report = await _report("Synthetic sample", ClassificationCorpus.synthetic(), with_cases=True)

    assert not report.missed_targets(), report.missed_targets()


@pytest.mark.asyncio
@pytest.mark.skipif(not _CORPUS, reason="DOCUMENT_CLASSIFICATION_CORPUS names no label file of real documents")
async def test_the_real_invoices_meet_the_targets() -> None:
    cases = await ClassificationCorpus.from_label_file(Path(str(_CORPUS)))

    report = await _report("Real documents", cases, with_cases=False)

    assert not report.missed_targets(), report.missed_targets()
