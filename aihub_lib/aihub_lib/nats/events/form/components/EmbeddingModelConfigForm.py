"""Form component for embedding model configuration."""

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.elements.Group import Group
from aihub_lib.nats.events.form.helpers import create_model_select_field


def create_embedding_model_config_form(name: str = "embed_model") -> Group:
    """
    Creates a form group for embedding model configuration.

    This matches the EmbeddingModelConfig Pydantic model structure.

    Args:
        name: The form field name (default: "embed_model" to match retriever config structure)
    """
    return Group(
        name=name,
        label=LocaleString(
            en="Embedding Model",
            de="Einbettungsmodell",
            fr="Modèle d'embedding",
            it="Modello di embedding",
        ),
        children=[
            create_model_select_field(
                name="model_name",
                label=LocaleString(
                    en="Model Name",
                    de="Modellname",
                    fr="Nom du modèle",
                    it="Nome del modello",
                ),
                options_api_mode="embedding",
                help_text=LocaleString(
                    en="The embedding model for vector search.",
                    de="Das Einbettungsmodell für die Vektorsuche.",
                    fr="Le modèle d'embedding pour la recherche vectorielle.",
                    it="Il modello di embedding per la ricerca vettoriale.",
                ),
            ),
        ],
    )
