"""Form component for LLM configuration (model selection + parameters)."""

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.components.LLMParameterForm import create_llm_parameter_form
from aihub_lib.nats.events.form.elements.Group import Group
from aihub_lib.nats.events.form.helpers import create_model_select_field


def create_llm_config_form(name: str = "llm") -> Group:
    """
    Creates a form group for full LLM configuration (model + parameters).

    This matches the LLMConfig Pydantic model structure with nested LLMParameter.

    Args:
        name: The form field name (default: "llm" to match common config structures)
    """
    return Group(
        name=name,
        label=LocaleString(
            en="LLM Configuration",
            de="LLM-Konfiguration",
            fr="Configuration LLM",
            it="Configurazione LLM",
        ),
        children=[
            create_model_select_field(
                name="model_name",
                label=LocaleString(
                    en="Model",
                    de="Modell",
                    fr="Modèle",
                    it="Modello",
                ),
                options_api_mode="chat",
                help_text=LocaleString(
                    en="The language model to use for generating responses.",
                    de="Das Sprachmodell für die Generierung von Antworten.",
                    fr="Le modèle de langage pour générer des réponses.",
                    it="Il modello di linguaggio per generare risposte.",
                ),
            ),
            create_llm_parameter_form(),
        ],
    )
