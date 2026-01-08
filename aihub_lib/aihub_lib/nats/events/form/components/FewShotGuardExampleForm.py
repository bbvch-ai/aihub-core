"""Form component for few-shot guard examples."""

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.elements.Checkbox import Checkbox
from aihub_lib.nats.events.form.elements.Repeater import Repeater
from aihub_lib.nats.events.form.helpers import create_locale_string_group


def create_few_shot_guard_examples_form(name: str = "few_shot_guard_examples") -> Repeater:
    """
    Creates a Repeater form for FewShotGuardExample list.

    This matches the list[FewShotGuardExample] structure used in agent configs.
    Each example contains a user message, success flag, and reason - all with LocaleString support.

    Args:
        name: The form field name (default: "few_shot_guard_examples")
    """
    return Repeater(
        name=name,
        label=LocaleString(
            en="Few-Shot Guard Examples",
            de="Few-Shot-Guard-Beispiele",
            fr="Exemples de garde few-shot",
            it="Esempi di guardia few-shot",
        ),
        add_label=LocaleString(
            en="Add Example",
            de="Beispiel hinzufügen",
            fr="Ajouter un exemple",
            it="Aggiungi esempio",
        ),
        children=[
            create_locale_string_group(
                name="user",
                label=LocaleString(
                    en="User Message",
                    de="Benutzernachricht",
                    fr="Message utilisateur",
                    it="Messaggio utente",
                ),
                input_type="text",
            ),
            Checkbox(
                name="success",
                label=LocaleString(
                    en="Should Accept",
                    de="Sollte akzeptieren",
                    fr="Devrait accepter",
                    it="Dovrebbe accettare",
                ),
                help=LocaleString(
                    en="Whether this type of request should be accepted (true) or rejected (false).",
                    de="Ob diese Art von Anfrage akzeptiert (wahr) oder abgelehnt (falsch) werden soll.",
                    fr="Si ce type de demande doit être accepté (vrai) ou rejeté (faux).",
                    it="Se questo tipo di richiesta deve essere accettata (vero) o rifiutata (falso).",
                ),
                binary=True,
            ),
            create_locale_string_group(
                name="reason",
                label=LocaleString(
                    en="Reason",
                    de="Begründung",
                    fr="Raison",
                    it="Motivo",
                ),
                input_type="text",
            ),
        ],
    )
