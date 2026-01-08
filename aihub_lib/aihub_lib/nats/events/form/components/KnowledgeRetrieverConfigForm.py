"""Form component for knowledge retriever configuration."""

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.components.EmbeddingModelConfigForm import create_embedding_model_config_form
from aihub_lib.nats.events.form.elements.Group import Group
from aihub_lib.nats.events.form.elements.InputNumber import InputNumber
from aihub_lib.nats.events.form.elements.InputText import InputText
from aihub_lib.nats.events.form.elements.MultiSelect import MultiSelect
from aihub_lib.nats.events.form.elements.Select import Select


def create_retriever_type_select() -> Select:
    """Creates a select field for choosing between knowledge and insight retriever types."""
    return Select(
        name="retriever_type",
        label=LocaleString(
            en="Retriever Type",
            de="Retriever-Typ",
            fr="Type de récupérateur",
            it="Tipo di recuperatore",
        ),
        help=LocaleString(
            en="The type of retriever (knowledge or insight).",
            de="Der Typ des Retrievers (Wissen oder Einsicht).",
            fr="Le type de récupérateur (connaissance ou insight).",
            it="Il tipo di recuperatore (conoscenza o insight).",
        ),
        options=[
            {"label": "Knowledge", "value": "knowledge"},
            {"label": "Insight", "value": "insight"},
        ],
        option_label="label",
        option_value="value",
    )


def create_knowledge_retriever_config_form(name: str = "0") -> Group:
    """
    Creates a form group for KnowledgeRetrieverConfig.

    This matches the KnowledgeRetrieverConfig Pydantic model structure.

    Args:
        name: The form field name (default: "0" for array index in retrievers list)
    """
    return Group(
        name=name,
        label=LocaleString(
            en="Knowledge Retriever",
            de="Wissens-Retriever",
            fr="Récupérateur de connaissances",
            it="Recuperatore di conoscenza",
        ),
        children=[
            create_retriever_type_select(),
            create_embedding_model_config_form(),
            InputText(
                name="index_namespaces",
                label=LocaleString(
                    en="Index Namespaces",
                    de="Index-Namespaces",
                    fr="Espaces de noms d'index",
                    it="Namespace degli indici",
                ),
                help=LocaleString(
                    en="Comma-separated list of namespaces to retrieve from.",
                    de="Kommagetrennte Liste der Namespaces für den Abruf.",
                    fr="Liste de namespaces séparés par des virgules.",
                    it="Elenco di namespace separati da virgole.",
                ),
            ),
            InputNumber(
                name="retrieve_k",
                label=LocaleString(
                    en="Documents to Retrieve",
                    de="Abzurufende Dokumente",
                    fr="Documents à récupérer",
                    it="Documenti da recuperare",
                ),
                help=LocaleString(
                    en="The number of documents to retrieve per query (1-100).",
                    de="Die Anzahl der Dokumente pro Abfrage (1-100).",
                    fr="Le nombre de documents à récupérer par requête (1-100).",
                    it="Il numero di documenti da recuperare per query (1-100).",
                ),
                min=1,
                max=100,
                step=1,
                show_buttons=True,
            ),
            Select(
                name="query_mode",
                label=LocaleString(
                    en="Query Mode",
                    de="Abfragemodus",
                    fr="Mode de requête",
                    it="Modalità di query",
                ),
                help=LocaleString(
                    en="How the vector store should be queried.",
                    de="Wie der Vektorspeicher abgefragt werden soll.",
                    fr="Comment le magasin de vecteurs doit être interrogé.",
                    it="Come deve essere interrogato il vector store.",
                ),
                options=[
                    {"label": "Default", "value": "default"},
                    {"label": "Hybrid", "value": "hybrid"},
                    {"label": "Sparse", "value": "sparse"},
                ],
                option_label="label",
                option_value="value",
            ),
            MultiSelect(
                name="node_types",
                label=LocaleString(
                    en="Node Types",
                    de="Knotentypen",
                    fr="Types de nœuds",
                    it="Tipi di nodo",
                ),
                help=LocaleString(
                    en="The types of nodes to retrieve (summary and/or content).",
                    de="Die Arten der abzurufenden Knoten (Zusammenfassung und/oder Inhalt).",
                    fr="Les types de nœuds à récupérer (résumé et/ou contenu).",
                    it="I tipi di nodi da recuperare (riepilogo e/o contenuto).",
                ),
                options=[
                    {"label": "Content", "value": "content"},
                    {"label": "Summary", "value": "summary"},
                ],
                option_label="label",
                option_value="value",
            ),
        ],
    )
