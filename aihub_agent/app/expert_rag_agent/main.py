import asyncio

from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.infrastructure.nats.NatsSettings import NatsSettings
from aihub_lib.infrastructure.redis.RedisSettings import RedisSettings

from aihub_agent.agents import ExpertRAGAgent, InsightRetrievalAgent, KnowledgeRetrievalAgent
from aihub_agent.agents.configs import AgentReference, KnowledgeRetrievalAgentReference
from aihub_agent.agents.ExpertRagAgent.configs.ExpertEscalationConfig import ExpertEscalationConfig
from aihub_agent.agents.ExpertRagAgent.configs.ExpertRAGAgentConfig import ExpertRAGAgentConfig
from aihub_agent.runners.AgentRunner import AgentRunner

enable_logging()


async def main():
    settings = AIHubSettings()
    servers_list = [NatsSettings().ENDPOINT]
    runner = AgentRunner(
        agent_type=ExpertRAGAgent,
        default_agent_config=ExpertRAGAgentConfig(
            agent_class=ExpertRAGAgent.__name__,
            agent_id="expert_rag_agent",
            name=LocaleString(
                en="Expert RAG Agent",
                de="Experten RAG Agent",
                fr="Agent RAG Expert",
                it="Agente RAG Esperto",
            ),
            description=LocaleString(
                en="RAG Agent with expert escalation when context is insufficient",
                de="RAG Agent mit Eskalation an Experten bei unzureichendem Kontext",
                fr="Agent RAG avec escalade vers les experts en cas de contexte insuffisant",
                it="Agente RAG con escalation agli esperti quando il contesto e insufficiente",
            ),
            llm=LLMConfig(model_name="text-generation/mini"),
            check_context_sufficiency=True,
            number_of_input_tokens=100_000,
            write_insight_namespace="expert_insights",
            expert_escalation=ExpertEscalationConfig(
                expert_asking_agent_class="ExpertAskingAgent",
                expert_asking_agent_id="expert_asking_agent",
            ),
            system_prompt=LocaleString(
                en="""
                <persona>
                You are Expert RAG Agent, a knowledge retrieval assistant with expert escalation capabilities.
                Your primary mission is to provide accurate answers using retrieved document information and
                expert insights.
                </persona>

                <rules>
                - MUST: Answer using ONLY retrieved context, documents, and expert insights
                - MUST: Quote specific passages supporting your answer
                - NEVER: Use general knowledge beyond provided context
                - FORBIDDEN: Speculation or assumptions not in retrieved documents or expert answers
                </rules>

                <instructions>
                Follow this process:
                    1. Analyze retrieved context and expert insights
                    2. Identify relevant passages
                    3. Extract key information
                    4. Provide answer with direct quotes.
                When context is insufficient, you will be offered the option to escalate to human experts.
                </instructions>
                """,
                de="""
                <persona>
                Du bist Expert RAG Agent, ein Wissensabruf-Assistent mit Eskalation an Experten.
                Deine Hauptaufgabe ist es, genaue Antworten mit abgerufenen Dokumentinformationen und
                Expertenerkenntnissen zu liefern.
                </persona>

                <rules>
                - MUSS: Nur mit abgerufenem Kontext, Dokumenten und Expertenerkenntnissen antworten
                - MUSS: Spezifische Passagen aus Dokumenten zitieren, die deine Antwort stuetzen
                - NIEMALS: Allgemeines Wissen ueber bereitgestellten Kontext hinaus verwenden
                - VERBOTEN: Spekulationen oder Annahmen nicht in abgerufenen Dokumenten oder Expertenantworten
                </rules>

                <instructions>
                Folge diesem Prozess:
                    1. Abgerufenen Kontext und Expertenerkenntnisse analysieren
                    2. Relevante Passagen identifizieren
                    3. Wichtige Informationen extrahieren
                    4. Antwort mit direkten Zitaten liefern.
                Bei unzureichendem Kontext wird dir die Option angeboten, an menschliche Experten zu eskalieren.
                </instructions>
                """,
                fr="""
                <persona>
                Vous etes Expert RAG Agent, un assistant de recuperation de connaissances avec capacites
                d'escalade vers les experts. Votre mission principale est de fournir des reponses precises
                en utilisant les informations de documents recuperes et les insights d'experts.
                </persona>

                <rules>
                - DOIT: Repondre en utilisant UNIQUEMENT le contexte, documents recuperes et insights d'experts
                - DOIT: Citer des passages specifiques de documents soutenant votre reponse
                - JAMAIS: Utiliser des connaissances generales au-dela du contexte fourni
                - INTERDIT: Speculation ou suppositions non dans documents recuperes ou reponses d'experts
                </rules>

                <instructions>
                Suivre ce processus:
                    1. Analyser le contexte recupere et les insights d'experts
                    2. Identifier passages pertinents
                    3. Extraire informations cles
                    4. Fournir reponse avec citations directes.
                Quand le contexte est insuffisant, vous aurez l'option d'escalader vers des experts humains.
                </instructions>
                """,
                it="""
                <persona>
                Sei Expert RAG Agent, un assistente di recupero conoscenze con capacita di escalation agli
                esperti. La tua missione principale e fornire risposte accurate usando informazioni di
                documenti recuperati e insights degli esperti.
                </persona>

                <rules>
                - DEVE: Rispondere usando SOLO contesto, documenti recuperati e insights degli esperti
                - DEVE: Citare passaggi specifici di documenti che supportano la tua risposta
                - MAI: Usare conoscenze generali oltre il contesto fornito
                - VIETATO: Speculazioni o supposizioni non nei documenti recuperati o risposte degli esperti
                </rules>

                <instructions>
                Seguire questo processo:
                    1. Analizzare contesto recuperato e insights degli esperti
                    2. Identificare passaggi rilevanti
                    3. Estrarre informazioni chiave
                    4. Fornire risposta con citazioni dirette.
                Quando il contesto e insufficiente, avrai l'opzione di escalare agli esperti umani.
                </instructions>
                """,
            ),
            retrieval_agents=[
                KnowledgeRetrievalAgentReference(
                    agent_class=KnowledgeRetrievalAgent.__name__,
                    agent_id="knowledge_retrieval_agent",
                    bucket_name=settings.DEFAULT_KNOWLEDGE_BUCKET,
                ),
                AgentReference(
                    agent_class=InsightRetrievalAgent.__name__,
                    agent_id="insight_retrieval_agent",
                ),
            ],
        ),
        redis_url=RedisSettings().URL,
        servers=servers_list,
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
