"""Form component for LLM parameter configuration."""

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.elements.Checkbox import Checkbox
from aihub_lib.nats.events.form.elements.Group import Group
from aihub_lib.nats.events.form.elements.InputNumber import InputNumber
from aihub_lib.nats.events.form.elements.Slider import Slider


def create_llm_parameter_form(name: str = "default_parameter") -> Group:
    """
    Creates a form group for LLM parameters (temperature, logprobs, timeout).

    This matches the LLMParameter Pydantic model structure.

    Args:
        name: The form field name (default: "default_parameter" to match LLMConfig structure)
    """
    return Group(
        name=name,
        label=LocaleString(
            en="LLM Parameters",
            de="LLM-Parameter",
            fr="Paramètres LLM",
            it="Parametri LLM",
        ),
        children=[
            Slider(
                name="temperature",
                label=LocaleString(
                    en="Temperature",
                    de="Temperatur",
                    fr="Température",
                    it="Temperatura",
                ),
                help=LocaleString(
                    en="Controls randomness. Lower = more deterministic, higher = more creative.",
                    de="Steuert die Zufälligkeit. Niedriger = deterministischer, höher = kreativer.",
                    fr="Contrôle l'aléatoire. Bas = déterministe, haut = créatif.",
                    it="Controlla la casualità. Basso = deterministico, alto = creativo.",
                ),
                min=0.0,
                max=2.0,
                step=0.1,
            ),
            Checkbox(
                name="logprobs",
                label=LocaleString(
                    en="Return Log Probabilities",
                    de="Log-Wahrscheinlichkeiten zurückgeben",
                    fr="Retourner les probabilités logarithmiques",
                    it="Restituisci probabilità logaritmiche",
                ),
                help=LocaleString(
                    en="Whether to return log probabilities per token.",
                    de="Ob Log-Wahrscheinlichkeiten pro Token zurückgegeben werden.",
                    fr="Retourner ou non les probabilités logarithmiques par token.",
                    it="Se restituire le probabilità logaritmiche per token.",
                ),
                binary=True,
            ),
            InputNumber(
                name="top_logprobs",
                label=LocaleString(
                    en="Top Log Probabilities",
                    de="Top-Log-Wahrscheinlichkeiten",
                    fr="Top probabilités logarithmiques",
                    it="Top probabilità logaritmiche",
                ),
                help=LocaleString(
                    en="Number of top token log probabilities to return (0-20).",
                    de="Anzahl der Top-Token-Log-Wahrscheinlichkeiten (0-20).",
                    fr="Nombre de probabilités logarithmiques des tokens à retourner (0-20).",
                    it="Numero di probabilità logaritmiche dei token da restituire (0-20).",
                ),
                min=0,
                max=20,
                step=1,
                show_buttons=True,
            ),
            InputNumber(
                name="timeout",
                label=LocaleString(
                    en="API Timeout (seconds)",
                    de="API-Timeout (Sekunden)",
                    fr="Délai d'attente API (secondes)",
                    it="Timeout API (secondi)",
                ),
                help=LocaleString(
                    en="Timeout in seconds for API requests. Default: 600.0",
                    de="Timeout in Sekunden für API-Anfragen. Standard: 600.0",
                    fr="Délai d'attente en secondes pour les requêtes API. Par défaut: 600.0",
                    it="Timeout in secondi per le richieste API. Default: 600.0",
                ),
                min=0,
                max=3600,
                step=10,
                show_buttons=True,
            ),
        ],
    )
