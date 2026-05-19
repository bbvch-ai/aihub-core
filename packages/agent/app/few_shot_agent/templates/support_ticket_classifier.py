from swiss_ai_hub.core.generative_ai import FewShotExample, LLMConfig, LLMParameter
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.few_shot_agent import FewShotAgentConfig
from swiss_ai_hub.agent.steps.prompting.few_shot_step import FewShotStepConfig


def build() -> FewShotAgentConfig:
    return FewShotAgentConfig(
        agent_id="support-ticket-classifier",
        name=LocaleString(
            en="Support Ticket Classifier",
            de="Support-Ticket-Klassifizierer",
            fr="Classificateur de tickets support",
            it="Classificatore ticket di supporto",
        ),
        description=LocaleString(
            en="Classifies support tickets by category, priority, and suggested team assignment.",
            de="Klassifiziert Support-Tickets nach Kategorie, Priorität und Teamzuweisung.",
            fr="Classifie les tickets par catégorie, priorité et équipe suggérée.",
            it="Classifica i ticket per categoria, priorità e team suggerito.",
        ),
        icon="mage:tag",
        number_of_input_tokens=50000,
        llm=LLMConfig(
            model_name="text-generation/Qwen3-VL-235B-A22B-Instruct",
            default_parameter=LLMParameter(temperature=0.0, timeout=30.0),
        ),
        few_shot=FewShotStepConfig(
            system_prompt=LocaleString(
                en=(
                    "You are a support ticket triage system. Classify each ticket into exactly this format:\n\n"
                    "**Category:** <one of: Bug, Feature Request, Access Issue, Performance, Question, Data Issue>\n"
                    "**Priority:** <one of: Critical, High, Medium, Low>\n"
                    "**Team:** <one of: Engineering, DevOps, Security, Data, Product, Support>\n"
                    "**Summary:** <one sentence summarizing the core issue>\n\n"
                    "Be consistent and objective. Classify based on impact and urgency."
                ),
                de=(
                    "Du bist ein Support-Ticket-Triage-System. Klassifiziere jedes Ticket in genau diesem Format:\n\n"
                    "**Kategorie:** <Bug, Feature-Anfrage, Zugriffsproblem, Performance, Frage, Datenproblem>\n"
                    "**Priorität:** <Kritisch, Hoch, Mittel, Niedrig>\n"
                    "**Team:** <Engineering, DevOps, Security, Data, Product, Support>\n"
                    "**Zusammenfassung:** <Ein Satz zum Kernproblem>\n\n"
                    "Sei konsistent und objektiv."
                ),
                fr=(
                    "Vous êtes un système de triage de tickets. Classifiez chaque ticket dans ce format :\n\n"
                    "**Catégorie :** <Bug, Demande, Accès, Performance, Question, Données>\n"
                    "**Priorité :** <Critique, Haute, Moyenne, Basse>\n"
                    "**Équipe :** <Engineering, DevOps, Security, Data, Product, Support>\n"
                    "**Résumé :** <Une phrase résumant le problème>"
                ),
                it=(
                    "Sei un sistema di triage dei ticket. Classifica ogni ticket in questo formato:\n\n"
                    "**Categoria:** <Bug, Richiesta, Accesso, Performance, Domanda, Dati>\n"
                    "**Priorità:** <Critica, Alta, Media, Bassa>\n"
                    "**Team:** <Engineering, DevOps, Security, Data, Product, Support>\n"
                    "**Riepilogo:** <Una frase che riassume il problema>"
                ),
            ),
            few_shot_examples=[
                FewShotExample(
                    user=LocaleString(
                        en=(
                            "The production dashboard has been showing a blank page since this morning. "
                            "Multiple users across departments are affected. We can't access any analytics."
                        ),
                        de=(
                            "Das Produktions-Dashboard zeigt seit heute Morgen eine leere Seite. "
                            "Mehrere Benutzer in verschiedenen Abteilungen sind betroffen."
                        ),
                        fr=(
                            "Le tableau de bord de production affiche une page blanche depuis ce matin. "
                            "Plusieurs utilisateurs sont affectés."
                        ),
                        it=(
                            "La dashboard di produzione mostra una pagina vuota da stamattina. "
                            "Diversi utenti sono interessati."
                        ),
                    ),
                    agent=LocaleString(
                        en=(
                            "**Category:** Bug\n"
                            "**Priority:** Critical\n"
                            "**Team:** Engineering\n"
                            "**Summary:** Production dashboard completely inaccessible for multiple users, "
                            "blocking analytics access across departments."
                        ),
                        de=(
                            "**Kategorie:** Bug\n"
                            "**Priorität:** Kritisch\n"
                            "**Team:** Engineering\n"
                            "**Zusammenfassung:** Produktions-Dashboard für mehrere Benutzer nicht erreichbar, "
                            "Analytik-Zugang abteilungsübergreifend blockiert."
                        ),
                        fr=(
                            "**Catégorie :** Bug\n"
                            "**Priorité :** Critique\n"
                            "**Équipe :** Engineering\n"
                            "**Résumé :** Tableau de bord inaccessible pour plusieurs utilisateurs."
                        ),
                        it=(
                            "**Categoria:** Bug\n"
                            "**Priorità:** Critica\n"
                            "**Team:** Engineering\n"
                            "**Riepilogo:** Dashboard non accessibile per più utenti."
                        ),
                    ),
                ),
                FewShotExample(
                    user=LocaleString(
                        en=(
                            "It would be great if the report export could also support PDF format. "
                            "Currently we only have CSV and Excel."
                        ),
                        de=(
                            "Es wäre toll, wenn der Report-Export auch PDF unterstützen könnte. "
                            "Aktuell gibt es nur CSV und Excel."
                        ),
                        fr="Ce serait bien si l'export de rapports supportait aussi le format PDF.",
                        it="Sarebbe utile se l'esportazione dei report supportasse anche il formato PDF.",
                    ),
                    agent=LocaleString(
                        en=(
                            "**Category:** Feature Request\n"
                            "**Priority:** Low\n"
                            "**Team:** Product\n"
                            "**Summary:** Request to add PDF as an additional report export format alongside "
                            "existing CSV and Excel options."
                        ),
                        de=(
                            "**Kategorie:** Feature-Anfrage\n"
                            "**Priorität:** Niedrig\n"
                            "**Team:** Product\n"
                            "**Zusammenfassung:** Anfrage, PDF als zusätzliches Export-Format neben CSV und Excel "
                            "hinzuzufügen."
                        ),
                        fr=(
                            "**Catégorie :** Demande\n"
                            "**Priorité :** Basse\n"
                            "**Équipe :** Product\n"
                            "**Résumé :** Demande d'ajout du format PDF pour l'export de rapports."
                        ),
                        it=(
                            "**Categoria:** Richiesta\n"
                            "**Priorità:** Bassa\n"
                            "**Team:** Product\n"
                            "**Riepilogo:** Richiesta di aggiungere PDF come formato di esportazione."
                        ),
                    ),
                ),
                FewShotExample(
                    user=LocaleString(
                        en=(
                            "I joined the company last week and still can't access the internal knowledge base. "
                            "My manager already approved the request in the system."
                        ),
                        de=(
                            "Ich bin letzte Woche eingetreten und habe immer noch keinen Zugriff auf die "
                            "interne Wissensdatenbank. Mein Vorgesetzter hat die Anfrage bereits genehmigt."
                        ),
                        fr=(
                            "J'ai rejoint l'entreprise la semaine dernière et n'ai toujours pas accès "
                            "à la base de connaissances. Mon manager a approuvé la demande."
                        ),
                        it=(
                            "Sono entrato in azienda la settimana scorsa e non ho ancora accesso alla "
                            "knowledge base. Il mio responsabile ha già approvato la richiesta."
                        ),
                    ),
                    agent=LocaleString(
                        en=(
                            "**Category:** Access Issue\n"
                            "**Priority:** Medium\n"
                            "**Team:** Security\n"
                            "**Summary:** New employee unable to access knowledge base despite manager approval, "
                            "likely a provisioning delay."
                        ),
                        de=(
                            "**Kategorie:** Zugriffsproblem\n"
                            "**Priorität:** Mittel\n"
                            "**Team:** Security\n"
                            "**Zusammenfassung:** Neuer Mitarbeiter hat trotz Genehmigung keinen Zugriff, "
                            "vermutlich Bereitstellungsverzögerung."
                        ),
                        fr=(
                            "**Catégorie :** Accès\n"
                            "**Priorité :** Moyenne\n"
                            "**Équipe :** Security\n"
                            "**Résumé :** Nouvel employé sans accès malgré approbation du manager."
                        ),
                        it=(
                            "**Categoria:** Accesso\n"
                            "**Priorità:** Media\n"
                            "**Team:** Security\n"
                            "**Riepilogo:** Nuovo dipendente senza accesso nonostante l'approvazione."
                        ),
                    ),
                ),
            ],
        ),
    )
