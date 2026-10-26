# Knowledge extraction e2e fixtures

The corpus the Knowledge Extraction Agent's and the Universal Agent's document-table specs run against
(`e2e/tests/knowledge-extraction-agent/`, `e2e/tests/universal-agent/document-tables.spec.ts`), and its ground truth.
The corpus itself is generated, not committed; the ground truth is committed so a reviewer can read what each case
expects.

| Part                                      | What it exercises                                                                        |
| ----------------------------------------- | ---------------------------------------------------------------------------------------- |
| ACME, Globex, Initech invoices            | One table across many files, the path filter, follow-ups, the same path in two databases |
| `invoices/{2023,2024,2025}/hooli/…` (150) | A selection too large for one answer: sample, facets, parts, narrowing, the ceiling      |
| `invoices/2025/q2/vandelay-2025-001.md`   | A document longer than the full-read limit (600,000 characters): partial read            |
| `invoices/2025/q3/initrode-2025-0*.pdf`   | Hardware lines that never say "hardware", and borderline items                           |
| `legal/contracts/`                        | Supplier contracts: notice period, liability cap, governing law; one long contract       |
| `legal/slas/`                             | Service levels: response and resolution per priority, availability penalties             |

`ground_truth.json` lists the hardware lines per invoice (`borderline` marks items a reader may or may not count),
`ground_truth_contracts.json` the clauses per contract and `ground_truth_slas.json` the service levels per SLA.

## Seeding a dev stack

Needs the dev stack, the API on :8000 and the document ingestion pipeline (`make document-ingestion-pipeline` in
`packages/pipeline`). From the repository root, with `.env` loaded (`set -a; . ./.env; set +a`):

```bash
uv run --no-project --with reportlab --with python-docx --with openpyxl --with mongoengine --with boto3 --with httpx python e2e/fixtures/knowledge-extraction/generate_corpus.py
```

```bash
uv run --package swiss-ai-hub-core python e2e/fixtures/knowledge-extraction/setup_knowledge.py
```

```bash
uv run --package swiss-ai-hub-core python e2e/fixtures/knowledge-extraction/seed.py
```

```bash
uv run --package swiss-ai-hub-core python e2e/fixtures/knowledge-extraction/wait_ingested.py
```

`setup_knowledge.py` creates the knowledge databases `kxe2e` (collections `finance`, `legal`) and `kxe2eb` (`hr`);
`seed.py` puts the files into the data lake and announces them the way a source sync does, and accepts `collection path`
pairs to seed only some; `wait_ingested.py` waits until every file is ingested.

The specs read the database through `E2E_DOCUMENT_DATABASE` and `E2E_DOCUMENT_COLLECTION` (see
`e2e/tests/universal-agent/support/env.ts`) and skip with a message when they are not set. The contract and SLA specs
(`e2e/tests/knowledge-extraction-agent/legal-tables.spec.ts`) use the collection in `E2E_DOCUMENT_LEGAL_COLLECTION`
(`legal` by default) and score against `ground_truth_contracts.json` and `ground_truth_slas.json`. Like the Universal
Agent suite, they run by hand, not in CI, and spend model tokens.
