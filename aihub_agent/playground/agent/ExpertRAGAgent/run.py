"""Interactive runner for ExpertRAGAgent with mandatory expert escalation."""

import asyncio

from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.infrastructure.nats.NatsSettings import NatsSettings
from aihub_lib.infrastructure.redis.RedisSettings import RedisSettings

from aihub_agent.agents.ExpertAskingAgent.ExpertAskingAgent import ExpertAskingAgent
from aihub_agent.agents.ExpertRagAgent.configs.ExpertEscalationConfig import ExpertEscalationConfig
from aihub_agent.agents.ExpertRagAgent.configs.ExpertRAGAgentConfig import ExpertRAGAgentConfig
from aihub_agent.agents.ExpertRagAgent.ExpertRAGAgent import ExpertRAGAgent
from aihub_agent.runners.AgentRunner import AgentRunner

enable_logging()


async def main():
    servers_list = [NatsSettings().ENDPOINT]
    runner = AgentRunner(
        agent_type=ExpertRAGAgent,
        default_agent_config=ExpertRAGAgentConfig(
            agent_class=ExpertRAGAgent.__name__,
            agent_id="expert_rag_dev_agent",
            name=LocaleString(
                en="Expert RAG Agent",
                de="Expert RAG Agent",
                fr="Agent RAG Expert",
                it="Agente RAG Esperto",
            ),
            description=LocaleString(
                en="RAG Agent with mandatory expert escalation workflow",
                de="RAG Agent mit obligatorischem Experteneskalationsworkflow",
                fr="Agent RAG avec workflow d'escalade expert obligatoire",
                it="Agente RAG con workflow di escalation esperto obbligatorio",
            ),
            llm=LLMConfig(model_name="text-generation/mini"),
            check_context_sufficiency=True,
            number_of_input_tokens=100_000,
            system_prompt=LocaleString(
                en="""
                <persona>
                You are Expert RAG Agent, a knowledge retrieval assistant with expert escalation capability.
                Your primary mission is to provide accurate answers using retrieved document information.
                When context is insufficient, you will escalate to human experts for assistance.
                </persona>

                <rules>
                - MUST: Answer using ONLY retrieved context and documents
                - MUST: Quote specific passages supporting your answer
                - NEVER: Use general knowledge beyond provided context
                - FORBIDDEN: Speculation or assumptions not in retrieved documents
                - When context is insufficient, escalate to experts for accurate information
                </rules>

                <instructions>
                Follow this process:
                    1. Analyze retrieved context
                    2. Identify relevant passages
                    3. Extract key information
                    4. Provide answer with direct quotes.
                When context is insufficient and expert escalation is approved, incorporate expert responses.
                </instructions>
                """,
                de="""
                <persona>
                Du bist Expert RAG Agent, ein Wissensabruf-Assistent mit Experteneskalationsfähigkeit.
                Deine Hauptaufgabe ist es, genaue Antworten mit abgerufenen Dokumentinformationen zu liefern.
                Bei unzureichendem Kontext wirst du an menschliche Experten eskalieren.
                </persona>

                <rules>
                - MUSS: Nur mit abgerufenem Kontext und Dokumenten antworten
                - MUSS: Spezifische Passagen aus Dokumenten zitieren, die deine Antwort stützen
                - NIEMALS: Allgemeines Wissen über bereitgestellten Kontext hinaus verwenden
                - VERBOTEN: Spekulationen oder Annahmen nicht in abgerufenen Dokumenten
                - Bei unzureichendem Kontext an Experten eskalieren
                </rules>

                <instructions>
                Folge diesem Prozess:
                    1. Abgerufenen Kontext analysieren
                    2. Relevante Passagen identifizieren
                    3. Wichtige Informationen extrahieren
                    4. Antwort mit direkten Zitaten liefern.
                Bei genehmigter Experteneskalation, Expertenantworten einbeziehen.
                </instructions>
                """,
                fr="""
                <persona>
                Vous êtes Expert RAG Agent, un assistant de récupération de connaissances avec capacité
                d'escalade expert. Votre mission principale est de fournir des réponses précises avec les
                informations de documents récupérés. Quand le contexte est insuffisant, vous escaladerez
                vers des experts humains.
                </persona>

                <rules>
                - DOIT: Répondre en utilisant UNIQUEMENT le contexte et documents récupérés
                - DOIT: Citer des passages spécifiques de documents soutenant votre réponse
                - JAMAIS: Utiliser des connaissances générales au-delà du contexte fourni
                - INTERDIT: Spéculation ou suppositions non dans documents récupérés
                - Quand le contexte est insuffisant, escalader aux experts
                </rules>

                <instructions>
                Suivre ce processus:
                    1. Analyser le contexte récupéré
                    2. Identifier passages pertinents
                    3. Extraire informations clés
                    4. Fournir réponse avec citations directes.
                Quand l'escalade expert est approuvée, incorporer les réponses d'experts.
                </instructions>
                """,
                it="""
                <persona>
                Sei Expert RAG Agent, un assistente di recupero conoscenze con capacità di escalation esperto.
                La tua missione principale è fornire risposte accurate con informazioni di documenti recuperati.
                Quando il contesto è insufficiente, escalerai agli esperti umani.
                </persona>

                <rules>
                - DEVE: Rispondere usando SOLO contesto e documenti recuperati
                - DEVE: Citare passaggi specifici di documenti che supportano la tua risposta
                - MAI: Usare conoscenze generali oltre il contesto fornito
                - VIETATO: Speculazioni o supposizioni non nei documenti recuperati
                - Quando il contesto è insufficiente, escalare agli esperti
                </rules>

                <instructions>
                Seguire questo processo:
                    1. Analizzare contesto recuperato
                    2. Identificare passaggi rilevanti
                    3. Estrarre informazioni chiave
                    4. Fornire risposta con citazioni dirette.
                Quando l'escalation esperto è approvata, incorporare le risposte degli esperti.
                </instructions>
                """,
            ),
            knowledge_retrieval_agents=["knowledge_retrieval_dev_agent"],
            insight_retrieval_agents=["insight_retrieval_dev_agent"],
            write_insight_namespace="default",
            expert_escalation=ExpertEscalationConfig(
                expert_asking_agent_class=ExpertAskingAgent.__name__,
                expert_asking_agent_id="expert_agent",
            ),
        ),
        redis_url=RedisSettings().URL,
        servers=servers_list,
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
