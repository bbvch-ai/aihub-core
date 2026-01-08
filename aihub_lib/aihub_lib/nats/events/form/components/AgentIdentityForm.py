"""Form component for agent identity fields (name, description, icon, class, id)."""

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form import ALL_FORM_OPTIONS
from aihub_lib.nats.events.form.elements.InputText import InputText
from aihub_lib.nats.events.form.helpers import create_locale_string_group


def create_agent_identity_form() -> list[ALL_FORM_OPTIONS]:
    """
    Creates form elements for agent identity fields.

    This includes:
    - name (LocaleString): Display name in 4 languages
    - description (LocaleString): Description in 4 languages
    - icon: Icon identifier string
    - agent_class: Read-only agent class name
    - agent_id: Read-only agent instance ID

    Returns a flat list of form elements to be extended into the main form.
    """
    return [
        create_locale_string_group(
            name="name",
            label=LocaleString(
                en="Agent Name",
                de="Agent-Name",
                fr="Nom de l'agent",
                it="Nome dell'agente",
            ),
            input_type="text",
            help_text=LocaleString(
                en="Display name for the agent",
                de="Anzeigename des Agenten",
                fr="Nom d'affichage de l'agent",
                it="Nome visualizzato dell'agente",
            ),
        ),
        create_locale_string_group(
            name="description",
            label=LocaleString(
                en="Agent Description",
                de="Agent-Beschreibung",
                fr="Description de l'agent",
                it="Descrizione dell'agente",
            ),
            input_type="textarea",
            rows=3,
            help_text=LocaleString(
                en="Description of what the agent does",
                de="Beschreibung, was der Agent macht",
                fr="Description de ce que fait l'agent",
                it="Descrizione di ciò che fa l'agente",
            ),
        ),
        InputText(
            name="icon",
            label=LocaleString(
                en="Icon",
                de="Symbol",
                fr="Icône",
                it="Icona",
            ),
            help=LocaleString(
                en="Icon identifier (e.g., 'meteor-icons:robot')",
                de="Symbolkennung (z.B. 'meteor-icons:robot')",
                fr="Identifiant d'icône (par ex. 'meteor-icons:robot')",
                it="Identificatore dell'icona (es. 'meteor-icons:robot')",
            ),
        ),
        InputText(
            name="agent_class",
            label=LocaleString(
                en="Agent Class",
                de="Agent-Klasse",
                fr="Classe de l'agent",
                it="Classe dell'agente",
            ),
            help=LocaleString(
                en="The class name of the agent (read-only)",
                de="Der Klassenname des Agenten (schreibgeschützt)",
                fr="Le nom de la classe de l'agent (lecture seule)",
                it="Il nome della classe dell'agente (sola lettura)",
            ),
            disabled=True,
        ),
        InputText(
            name="agent_id",
            label=LocaleString(
                en="Agent ID",
                de="Agent-ID",
                fr="ID de l'agent",
                it="ID dell'agente",
            ),
            help=LocaleString(
                en="The unique identifier of the agent (read-only)",
                de="Die eindeutige Kennung des Agenten (schreibgeschützt)",
                fr="L'identifiant unique de l'agent (lecture seule)",
                it="L'identificatore univoco dell'agente (sola lettura)",
            ),
            disabled=True,
        ),
    ]
