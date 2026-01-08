"""Form component for reranking configuration."""

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.elements.Checkbox import Checkbox
from aihub_lib.nats.events.form.elements.Group import Group
from aihub_lib.nats.events.form.elements.InputNumber import InputNumber
from aihub_lib.nats.events.form.helpers import create_model_select_field


def create_reranking_model_form(name: str = "reranking_model") -> Group:
    """
    Creates a form group for RerankingModelConfig.

    Args:
        name: The form field name (default: "reranking_model")
    """
    return Group(
        name=name,
        label=LocaleString(
            en="Reranking Model",
            de="Reranking-Modell",
            fr="Modèle de reclassement",
            it="Modello di riordinamento",
        ),
        children=[
            create_model_select_field(
                name="model_name",
                label=LocaleString(
                    en="Reranking Model",
                    de="Reranking-Modell",
                    fr="Modèle de reclassement",
                    it="Modello di riordinamento",
                ),
                options_api_mode="rerank",
                help_text=LocaleString(
                    en="The model to use for reranking documents.",
                    de="Das Modell für das Reranking von Dokumenten.",
                    fr="Le modèle pour le reclassement des documents.",
                    it="Il modello per il riordinamento dei documenti.",
                ),
            ),
            InputNumber(
                name="top_n",
                label=LocaleString(
                    en="Top N Documents",
                    de="Top N Dokumente",
                    fr="Top N documents",
                    it="Top N documenti",
                ),
                help=LocaleString(
                    en="Number of top documents to keep after reranking (1-100).",
                    de="Anzahl der Top-Dokumente nach dem Reranking (1-100).",
                    fr="Nombre de documents à conserver après le reclassement (1-100).",
                    it="Numero di documenti da mantenere dopo il riordinamento (1-100).",
                ),
                min=1,
                max=100,
                step=1,
                show_buttons=True,
            ),
        ],
    )


def create_reranking_config_form(name: str = "reranking_config") -> Group:
    """
    Creates a form group for RerankingConfig (enabled flag + model config).

    This matches the RerankingConfig Pydantic model structure.

    Args:
        name: The form field name (default: "reranking_config")
    """
    return Group(
        name=name,
        label=LocaleString(
            en="Reranking Configuration",
            de="Reranking-Konfiguration",
            fr="Configuration du reclassement",
            it="Configurazione riordinamento",
        ),
        children=[
            Checkbox(
                name="enabled",
                label=LocaleString(
                    en="Enable Reranking",
                    de="Reranking aktivieren",
                    fr="Activer le reclassement",
                    it="Abilita riordinamento",
                ),
                help=LocaleString(
                    en="When enabled, retrieved documents will be reranked for improved relevance.",
                    de="Wenn aktiviert, werden Dokumente für bessere Relevanz neu geordnet.",
                    fr="Les documents récupérés seront reclassés pour une meilleure pertinence.",
                    it="I documenti recuperati verranno riordinati per una migliore rilevanza.",
                ),
                binary=True,
            ),
            create_reranking_model_form(),
        ],
    )
