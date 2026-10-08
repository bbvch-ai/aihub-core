# Runtime Record Schemas for Structured Extraction

Extends `2026_07_13_response_format_as_default_structured_output`.

## Context

Agents need to pull structured records out of whole documents, such as the billing lines of an invoice or the service
levels of an SLA (issue #1949, consumed by the extraction agent in #1888). Two things make this different from every
structured LLM call the platform already makes:

1. **The record shape is only known at request time.** Every existing `astructured_predict` caller uses a Pydantic model
   written at development time. Here the user's message decides the fields.
2. **One document holds zero, one or many records, and can exceed the model's context window.**

Strict structured output, the default since `2026_07_13`, puts every property into `required`. A field the model cannot
fill must therefore still be emittable, or the model cannot close the JSON object and pads to its output limit.

## Decision Drivers

- **Same structured-output path as everything else.** No second mechanism for dynamic schemas.
- **A schema must survive a workflow event.** The step that builds it and the fan-out steps that extract with it run
  separately, so the schema cannot be a generated class.
- **One failing document must not cost a run its other documents.**
- **Consistency of the schema across runs.** A field named or typed differently changes every table built from it.

## Decision

**1. The schema is plain data, rebuilt into a model by jambo.** `RecordSchema` is a list of `RecordField` (name,
primitive type, description). `to_records_model()` builds the record model with `swiss_ai_hub.jambo.SchemaConverter`,
the converter the API already uses for form submissions, and wraps it in a list. jambo becomes a dependency of
`packages/core`. Only `string`, `number`, `integer` and `boolean` are allowed, because jambo reads nothing but
`properties` and would silently drop a nested or free-form value.

**2. Every field is nullable and required.** The JSON schema types each property as `[type, "null"]` and lists all of
them in `required`, which is the only shape strict mode accepts for "the document does not say". The extraction prompt
names every field individually, as the structured-output guidance requires.

**3. Schema rules are checked after parsing, not in Pydantic validators.** `ResilientOpenAILike` retries on validation
errors, and an identical request at temperature zero returns the same schema. `RecordSchema.validated()` reports every
problem at once instead. Field names are normalised during parsing, which never fails.

**4. The schema model and the extraction model are separate parameters.** `RecordSchemaBuilder.build` takes its own LLM
and calls a temperature-zero copy of it. Measured on 2026-10-02 with the invoice description from #1949, five runs per
model:

| Model                | Runs sharing one schema | Differs from the majority             |
| -------------------- | ----------------------- | ------------------------------------- |
| gemma-4-31B-it       | 5/5                     | none                                  |
| Apertus-70B-Instruct | 5/5                     | none                                  |
| Kimi-K2.6            | 5/5                     | none                                  |
| Ministral-3-14B      | 5/5                     | names `invoice_date`, `supplier_name` |
| Qwen3.5-122B-A10B    | 5/5                     | types `amount` as string              |

Each model is consistent with itself, but models disagree with each other, so the schema model decides what a table
looks like. Keeping it separate lets a consuming agent pin it independently of the extraction model. The measurement is
reproducible with the consistency report in the module's integration tests.

**5. Filters are instructions, not fields.** A condition like "only hardware" goes to `RecordExtractor.extract` as
`instructions`, and the schema prompt tells the model not to turn it into a field.

**6. Long documents are split into overlapping windows.** A window is bounded by the input window minus the prompt, and
by half the output limit, because records come back as JSON that can reach twice the size of a dense table. Windows
overlap by ten percent. `RecordMerger` drops a record only when a *compatible* record came from the *adjacent* window:
non-null values agree, and the kept record takes the other's non-null values. Identical records within one window, or in
windows that share no text, are kept, because an invoice can legitimately repeat a line.

Every window after the first is also shown the document's opening, up to 512 tokens and at most half a window, as
context for values that apply to every record. An invoice states its number and supplier once, at the top. Without the
opening, records past the first window came back with those fields null, because the prompt forbids guessing. The model
takes such values from the opening only where the excerpt does not state them, and is told never to extract a record
from it. The cap of half a window keeps the opening inside the first window and before the second, so a record in it is
extracted once.

**7. Malformed output fails the document, not the run.** `RecordExtractor.extract` catches `ValueError` around each
model call and returns a `DocumentExtractionResult` with a `failure_reason`. A document fails as a whole, never with the
records of the windows that worked, because a partial list would read as complete. Infrastructure errors still raise.

### Considered and rejected

- **Letting the model return free-form JSON and parsing it leniently.** It abandons the strict path every other caller
  uses and moves validation into hand-written code.
- **Deduplicating on value equality across all windows.** It collapses genuinely repeated lines.
- **Filling null fields after extraction from values that are constant across the document's records.** A field set on
  only one line, such as a discount, would be copied to every record. The model can tell a header value from a line
  value; a post-processing rule cannot.
- **Passing only the schema to extraction.** The filter then has to be smuggled into field descriptions, which models do
  not reliably act on.

## Consequences

### Positive

- Any agent can extract records with a schema decided per request, with the same structured-output mechanism and cost
  tracking as every other call.
- A long document is extracted completely, and each record names the document it came from.

### Trade-offs

- **Windows sized by output are small.** On an 8192-token output limit a window holds about 4000 tokens, so a long
  document costs many calls.
- **A shared value must sit in the opening.** A value stated once in the middle of a long document, such as a section
  heading, still reaches only the records of its own window. A document that bundles several invoices may lend the
  first one's header to later records whose excerpt does not restate theirs.
- **Compatible-record matching can merge two distinct lines** that sit in adjacent windows and share every known value.
- **Page provenance is not available yet.** Parsed text carries no page boundaries, so `RecordProvenance.page` stays
  `None` until ingestion records them.
