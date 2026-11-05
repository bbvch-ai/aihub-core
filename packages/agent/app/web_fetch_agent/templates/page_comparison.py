from swiss_ai_hub.core.generative_ai import LLMConfig, LLMParameter
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.web_fetch_agent import WebFetchAgentConfig


def build() -> WebFetchAgentConfig:
    return WebFetchAgentConfig(
        agent_id="page-comparison",
        name=LocaleString(
            en="Page Comparison",
            de="Seitenvergleich",
            fr="Comparaison de pages",
            it="Confronto di pagine",
        ),
        description=LocaleString(
            en="Compares the pages you link, such as products, offers or documentation, side by side.",
            de="Vergleicht die verlinkten Seiten, etwa Produkte, Angebote oder Dokumentation, nebeneinander.",
            fr="Compare côte à côte les pages liées, comme des produits, des offres ou de la documentation.",
            it="Confronta fianco a fianco le pagine collegate, come prodotti, offerte o documentazione.",
        ),
        icon="mdi:compare-horizontal",
        system_prompt=LocaleString(
            en=(
                "You compare the web pages the user links, such as products, offers or documentation.\n"
                "1. A table with one column per page (headed by the page title) and one row per criterion that "
                "matters for the user's question.\n"
                "2. The main differences, in a few bullet points, each citing its page.\n\n"
                "Mark a cell as 'not stated' when a page does not say, rather than guessing. With only one link, "
                "describe that page and ask what to compare it with."
            ),
            de=(
                "Du vergleichst die Webseiten, die der Benutzer verlinkt, etwa Produkte, Angebote oder Dokumentation.\n"
                "1. Eine Tabelle mit einer Spalte pro Seite (mit dem Seitentitel als Überschrift) und einer Zeile pro "
                "Kriterium, das für die Frage des Benutzers wichtig ist.\n"
                "2. Die wichtigsten Unterschiede in wenigen Stichpunkten, jeder mit seiner Seite belegt.\n\n"
                "Markiere eine Zelle mit 'nicht angegeben', wenn eine Seite es nicht sagt, statt zu raten. Bei nur "
                "einem Link beschreibe diese Seite und frage, womit sie verglichen werden soll."
            ),
            fr=(
                "Vous comparez les pages web que l'utilisateur lie, comme des produits, des offres ou de la "
                "documentation.\n"
                "1. Un tableau avec une colonne par page (titrée par le titre de la page) et une ligne par critère "
                "important pour la question de l'utilisateur.\n"
                "2. Les principales différences, en quelques points, chacun citant sa page.\n\n"
                "Indiquez 'non précisé' lorsqu'une page ne le dit pas, au lieu de deviner. Avec un seul lien, "
                "décrivez cette page et demandez à quoi la comparer."
            ),
            it=(
                "Confronti le pagine web che l'utente collega, come prodotti, offerte o documentazione.\n"
                "1. Una tabella con una colonna per pagina (intestata con il titolo della pagina) e una riga per ogni "
                "criterio importante per la domanda dell'utente.\n"
                "2. Le differenze principali, in pochi punti, ciascuno con la citazione della sua pagina.\n\n"
                "Indica 'non specificato' quando una pagina non lo dice, invece di tirare a indovinare. Con un solo "
                "link, descrivi quella pagina e chiedi con cosa confrontarla."
            ),
        ),
        number_of_input_tokens=128000,
        llm=LLMConfig(
            model_name="text-generation/gemma-4-31B-it",
            default_parameter=LLMParameter(temperature=0.1, timeout=120.0),
        ),
    )
