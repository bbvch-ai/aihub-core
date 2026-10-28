from swiss_ai_hub.core.generative_ai import LLMConfig, LLMParameter
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.web_fetch_agent import WebFetchAgentConfig


def build() -> WebFetchAgentConfig:
    return WebFetchAgentConfig(
        agent_id="article-summariser",
        name=LocaleString(
            en="Article Summariser",
            de="Artikel-Zusammenfasser",
            fr="Résumeur d'articles",
            it="Riassuntore di articoli",
        ),
        description=LocaleString(
            en="Summarises the articles you link: key points first, then a short summary, with sources.",
            de=(
                "Fasst die verlinkten Artikel zusammen: zuerst die Kernpunkte, dann eine kurze Zusammenfassung, "
                "mit Quellen."
            ),
            fr="Résume les articles liés : d'abord les points clés, puis un court résumé, avec les sources.",
            it="Riassume gli articoli collegati: prima i punti chiave, poi un breve riassunto, con le fonti.",
        ),
        icon="mdi:text-box-search-outline",
        system_prompt=LocaleString(
            en=(
                "You summarise the web pages the user links. For each page:\n"
                "## <page title>\n"
                "- 3 to 5 key points, in plain language.\n"
                "- A two-sentence summary.\n\n"
                "Use only what the pages say, and cite the page behind each point. If the user asks a question "
                "about the pages, answer it first."
            ),
            de=(
                "Du fasst die Webseiten zusammen, die der Benutzer verlinkt. Für jede Seite:\n"
                "## <Seitentitel>\n"
                "- 3 bis 5 Kernpunkte in einfacher Sprache.\n"
                "- Eine Zusammenfassung in zwei Sätzen.\n\n"
                "Verwende nur, was auf den Seiten steht, und belege jeden Punkt mit seiner Seite. Stellt der "
                "Benutzer eine Frage zu den Seiten, beantworte sie zuerst."
            ),
            fr=(
                "Vous résumez les pages web que l'utilisateur lie. Pour chaque page :\n"
                "## <titre de la page>\n"
                "- 3 à 5 points clés, en langage simple.\n"
                "- Un résumé en deux phrases.\n\n"
                "Utilisez uniquement ce que disent les pages et citez la page de chaque point. Si l'utilisateur "
                "pose une question sur les pages, répondez-y d'abord."
            ),
            it=(
                "Riassumi le pagine web che l'utente collega. Per ogni pagina:\n"
                "## <titolo della pagina>\n"
                "- Da 3 a 5 punti chiave, in linguaggio semplice.\n"
                "- Un riassunto di due frasi.\n\n"
                "Usa solo ciò che dicono le pagine e cita la pagina di ogni punto. Se l'utente fa una domanda "
                "sulle pagine, rispondi prima a quella."
            ),
        ),
        number_of_input_tokens=128000,
        llm=LLMConfig(
            model_name="text-generation/gemma-4-31B-it",
            default_parameter=LLMParameter(temperature=0.2, timeout=120.0),
        ),
    )
