"""Form component for insight retriever configuration."""

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.components.KnowledgeRetrieverConfigForm import create_retriever_type_select
from aihub_lib.nats.events.form.elements.Group import Group
from aihub_lib.nats.events.form.elements.InputText import InputText


def create_insight_retriever_config_form(name: str = "1") -> Group:
    """
    Creates a form group for InsightRetrieverConfig.

    This matches the InsightRetrieverConfig Pydantic model structure.

    Args:
        name: The form field name (default: "1" for array index in retrievers list)
    """
    return Group(
        name=name,
        label=LocaleString(
            en="Insight Retriever",
            de="Einsichts-Retriever",
            fr="Récupérateur d'insights",
            it="Recuperatore di insight",
        ),
        children=[
            create_retriever_type_select(),
            InputText(
                name="namespace",
                label=LocaleString(
                    en="Namespace",
                    de="Namespace",
                    fr="Espace de noms",
                    it="Namespace",
                ),
                help=LocaleString(
                    en="The namespace to filter insights by.",
                    de="Der Namespace zum Filtern von Einsichten.",
                    fr="L'espace de noms pour filtrer les insights.",
                    it="Il namespace per filtrare gli insight.",
                ),
            ),
            InputText(
                name="agent_class",
                label=LocaleString(
                    en="Agent Class",
                    de="Agent-Klasse",
                    fr="Classe d'agent",
                    it="Classe agente",
                ),
                help=LocaleString(
                    en="The agent class to filter insights by.",
                    de="Die Agent-Klasse zum Filtern von Einsichten.",
                    fr="La classe d'agent pour filtrer les insights.",
                    it="La classe dell'agente per filtrare gli insight.",
                ),
            ),
            InputText(
                name="agent_id",
                label=LocaleString(
                    en="Agent ID",
                    de="Agent-ID",
                    fr="ID de l'agent",
                    it="ID agente",
                ),
                help=LocaleString(
                    en="The agent ID to filter insights by.",
                    de="Die Agent-ID zum Filtern von Einsichten.",
                    fr="L'ID de l'agent pour filtrer les insights.",
                    it="L'ID dell'agente per filtrare gli insight.",
                ),
            ),
        ],
    )
