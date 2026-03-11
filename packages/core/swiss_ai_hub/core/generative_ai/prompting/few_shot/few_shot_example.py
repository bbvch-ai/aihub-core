from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.core.form.elements.locale_input import LocaleInput
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class FewShotExample(Form):
    """
    A single few-shot example containing a user input and the expected agent response.

    Supports form duality pattern:
    - Data mode: LocaleString values for user and agent
    - Form mode: LocaleInput elements for user and agent (use as_form())
    """

    user: Annotated[
        LocaleString | LocaleInput,
        Field(description="The user's input in this example."),
    ]
    agent: Annotated[
        LocaleString | LocaleInput,
        Field(description="The agent's expected response to the user input."),
    ]

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode FewShotExample."""
        return cls(
            user=LocaleInput(
                label=LocaleString(
                    en="User Input",
                    de="Benutzereingabe",
                    fr="Entrée utilisateur",
                    it="Input utente",
                ),
                placeholder=LocaleString(
                    en="Example user message...",
                    de="Beispiel-Benutzernachricht...",
                    fr="Exemple de message utilisateur...",
                    it="Messaggio utente di esempio...",
                ),
                input_type="textarea",
                rows=2,
            ),
            agent=LocaleInput(
                label=LocaleString(
                    en="Agent Response",
                    de="Agentenantwort",
                    fr="Réponse de l'agent",
                    it="Risposta dell'agente",
                ),
                placeholder=LocaleString(
                    en="Expected agent response...",
                    de="Erwartete Agentenantwort...",
                    fr="Réponse attendue de l'agent...",
                    it="Risposta attesa dell'agente...",
                ),
                input_type="textarea",
                rows=2,
            ),
        )
