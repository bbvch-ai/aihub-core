from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.persistence.insight.InsightEntity import InsightCreator, InsightEntity
from llama_index.core.base.llms.types import ChatResponse
from llama_index.core.prompts import RichPromptTemplate

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.InsightAgent.events.InsightStartEvent import InsightStartEvent
from aihub_agent.agents.InsightAgent.events.InsightStopEvent import InsightStopEvent
from aihub_agent.agents.InsightAgent.InsightAgentConfig import InsightAgentConfig
from aihub_agent.i18n.AgentLocaleHandler import AgentLocaleHandler
from aihub_agent.workflow.decorators.step import step


class InsightAgent(Agent):
    """
    The InsightAgent processes expert conversations and extracts insights
    to store in MongoDB for future retrieval by RAG agents.

    This agent is triggered after the ExpertAskingAgent successfully obtains
    an answer from an expert, receiving the chat history and relevant nodes.
    """

    @step(
        name=LocaleString(en="Extract Insight"),
        description=LocaleString(en="Extracts structured insight from the expert conversation."),
        icon="carbon:data-enrichment",
    )
    async def extract_insight_step(
        self,
        event: InsightStartEvent,
        agent_config: InsightAgentConfig,
        displayer: EventDisplayer,
        t: AgentLocaleHandler,
    ) -> InsightStopEvent:
        """
        Extracts insights from the expert conversation and stores them in MongoDB.
        """
        await displayer.display_thought(t("agent.insight_agent.thoughts.extracting_insight"))

        # Generate insight from the expert conversation
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            chat = RichPromptTemplate(template_str=t("agent.insight_agent.extract_insight_prompt")).format_messages(
                chat_history=event.chat_history,
                question=event.question,
                expert_answer=event.expert_answer,
            )
            response: ChatResponse = await llm.achat(chat)
            insight_content = response.message.content

        # Generate a title for the insight
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            title_chat = RichPromptTemplate(
                template_str=t("agent.insight_agent.generate_title_prompt")
            ).format_messages(
                question=event.question,
                insight=insight_content,
            )
            title_response: ChatResponse = await llm.achat(title_chat)
            insight_title = title_response.message.content.strip().strip('"').strip("'")

        # Store the insight in MongoDB
        await displayer.display_thought(t("agent.insight_agent.thoughts.storing_insight"))

        creator = InsightCreator(
            agent_class=agent_config.agent_class,
            agent_id=agent_config.agent_id,
        )

        insight = InsightEntity.create_insight(
            title=insight_title,
            content=insight_content,
            question=event.question,
            expert_answer=event.expert_answer,
            namespace=agent_config.namespace,
            creator=creator,
        )

        await displayer.display_thought(t("agent.insight_agent.thoughts.insight_stored", insight_id=str(insight.id)))

        return InsightStopEvent(insight_stored=True, insight_id=str(insight.id))
