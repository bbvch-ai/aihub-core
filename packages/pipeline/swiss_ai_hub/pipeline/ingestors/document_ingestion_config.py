from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.form import Checkbox, ModelSelect
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.ingestors import IngestorConfig

_I18N = "lib.ingestors.document_ingestion.config"


class DocumentIngestionConfig(IngestorConfig):
    """
    What a knowledge database owned by the Generic Document Ingestion Pipeline can be configured with.

    Announced to the API as the pipeline's form, stored per database as ``BucketEntity.configuration`` and read back
    per run by ``model_builders``, which fills every key the row does not carry from the deployment's defaults — so
    databases created before a knob existed keep ingesting exactly as before. The text and embedding model are
    required on the form (pre-filled with the deployment default); the vision model is an opt-in override.

    A deployment that ships its own pipeline extends this class with further knobs and passes its ``as_form()`` to
    ``document_ingestion_pipeline_definitions(config=...)``; nothing in the API or the UI needs to change for that.
    """

    llm_model: Annotated[
        str | ModelSelect,
        Field(description="Text-generation model for summaries, table refinement and figure descriptions."),
    ]
    embedding_model: Annotated[
        str | ModelSelect,
        Field(
            description="Embedding model the chunks are indexed with. Immutable: the collection's dimension derives "
            "from it."
        ),
    ]
    vision_model: Annotated[
        str | ModelSelect | None,
        Field(description="Model that describes figures; the text model when unset."),
    ] = None
    with_summary_nodes: Annotated[
        bool | Checkbox | None, Field(description="Generate recursive summaries for hierarchical RAG.")
    ] = None
    with_table_refinement: Annotated[
        bool | Checkbox | None, Field(description="Refine tables with the text model to detect structure and split.")
    ] = None
    with_figure_descriptions: Annotated[
        bool | Checkbox | None, Field(description="Generate figure descriptions with the vision model.")
    ] = None

    @classmethod
    def as_form(
        cls,
        *,
        llm_model: Annotated[str, "Deployment default text model, pre-selected in the picker"],
        embedding_model: Annotated[str, "Deployment default embedding model, pre-selected in the picker"],
        vision_model: Annotated[str | None, "Deployment default vision model, if any"] = None,
        with_summary_nodes: bool = True,
        with_table_refinement: bool = True,
        with_figure_descriptions: bool = True,
    ) -> Self:
        """The announced form, pre-filled with the deployment's own defaults so a new database starts from them."""
        base = IngestorConfig.as_form()
        return cls(
            name=base.name,
            description=base.description,
            llm_model=ModelSelect(
                label=LocaleString.from_i18n_path(f"{_I18N}.llm_model.label"),
                help=LocaleString.from_i18n_path(f"{_I18N}.llm_model.help"),
                mode="chat",
                value=llm_model,
            ),
            embedding_model=ModelSelect(
                label=LocaleString.from_i18n_path(f"{_I18N}.embedding_model.label"),
                help=LocaleString.from_i18n_path(f"{_I18N}.embedding_model.help"),
                mode="embedding",
                value=embedding_model,
            ),
            vision_model=ModelSelect(
                label=LocaleString.from_i18n_path(f"{_I18N}.vision_model.label"),
                help=LocaleString.from_i18n_path(f"{_I18N}.vision_model.help"),
                mode="chat",
                value=vision_model,
            ),
            with_summary_nodes=Checkbox(
                label=LocaleString.from_i18n_path(f"{_I18N}.with_summary_nodes.label"),
                help=LocaleString.from_i18n_path(f"{_I18N}.with_summary_nodes.help"),
                value=with_summary_nodes,
            ),
            with_table_refinement=Checkbox(
                label=LocaleString.from_i18n_path(f"{_I18N}.with_table_refinement.label"),
                help=LocaleString.from_i18n_path(f"{_I18N}.with_table_refinement.help"),
                value=with_table_refinement,
            ),
            with_figure_descriptions=Checkbox(
                label=LocaleString.from_i18n_path(f"{_I18N}.with_figure_descriptions.label"),
                help=LocaleString.from_i18n_path(f"{_I18N}.with_figure_descriptions.help"),
                value=with_figure_descriptions,
            ),
        )
