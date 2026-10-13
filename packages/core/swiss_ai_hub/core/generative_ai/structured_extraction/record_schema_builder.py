from typing import Annotated

from llama_index.core.llms import LLM
from llama_index.core.prompts.rich import RichPromptTemplate

from swiss_ai_hub.core.generative_ai.structured_extraction.record_schema import DEFAULT_MAX_FIELDS, RecordSchema
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn

# A twenty-field schema measures well under a thousand tokens. The cap bounds what a strict-mode stall can cost,
# which is otherwise the model's whole output budget.
SCHEMA_PROPOSAL_MAX_TOKENS = 2048


class RecordSchemaBuilder:
    """Turns a natural-language description of the wanted data into the record schema to extract with.

    Takes its own model rather than the extraction model, because the schema is where model variance hurts most: a
    field named or typed differently changes every table built from it. Keeping the two apart lets each model be
    chosen, and its schema consistency measured, on its own.
    """

    @staticmethod
    @trace_fn
    async def build(
        description: Annotated[str, "What each record should hold, e.g. 'invoice number, date, supplier, amount'"],
        llm: Annotated[LLM, "Model that proposes the schema"],
        t: LocaleHandler,
        max_fields: Annotated[int, "Most fields the schema may have"] = DEFAULT_MAX_FIELDS,
    ) -> RecordSchema:
        """Raises `InvalidRecordSchemaError`, or a `ValueError` for malformed output, when no usable schema came back.

        Fails rather than degrading: without a schema there is nothing to extract, so the caller has to decide.
        """
        proposal = await RecordSchemaBuilder._deterministic(llm).astructured_predict(
            RecordSchema,
            RichPromptTemplate(t("lib.prompt.structured_extraction.schema_prompt")),
            description=description,
            max_fields=max_fields,
        )
        return proposal.validated(max_fields)

    @staticmethod
    def _deterministic(llm: LLM) -> LLM:
        """Temperature zero, so the same description yields the same columns from run to run.

        Set on a copy because a per-call `max_tokens` is discarded by `OpenAI._get_model_kwargs`, and the caller's
        instance must keep its own settings.
        """
        return llm.model_copy(update={"temperature": 0.0, "max_tokens": SCHEMA_PROPOSAL_MAX_TOKENS})
