import logging

from aihub_agent.agents.Agent import Agent
from aihub_lib.nats.events.user import UserMessageEvent
from aihub_lib.nats.events import StopEvent, LimitChatHistoryEvent, LLMStopEvent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.generative_ai.utils.limit_chat_history import limit_chat_history
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.generative_ai.utils.retrieve_nodes import retrieve_nodes
from aihub_lib.nats.events.semantic.retriever import RetrieverEvent
from llama_index.core import PromptTemplate
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from wiki_agent.WikiAgent.WikiAgentConfig import WikiAgentConfig
from wiki_agent.WikiAgent.event.AtLeastOneNodeEvent import AtLeastOneNodeEvent
from wiki_agent.WikiAgent.event.ZeroNodesEvent import ZeroNodesEvent

logger = logging.getLogger(__name__)


class WikiAgent(Agent):

    @step(
        name=LocaleString(en="Limit Chat History"),
        description=LocaleString(en="Truncates incoming chat messages to fit within the configured token limit"),
        icon="iconoir:cut",
    )
    async def limit_chat_history_step(
        self,
        event: UserMessageEvent,
        agent_config: WikiAgentConfig,
    ) -> LimitChatHistoryEvent:
        """
        Truncates incoming chat messages to fit within the configured token limit
        """
        print("limit_chat_history_step")
        limited_chat_history = limit_chat_history(
            chat_history=event.messages,
            number_of_input_tokens=agent_config.number_of_input_tokens,
        )
        return LimitChatHistoryEvent(limited_history=limited_chat_history)

    @step(
        name=LocaleString(en="Retrieve Nodes"),
        description=LocaleString(en="Retrieves relevant nodes from the knowledge base."),
        icon="iconoir:search",
    )
    async def retrieve_step(
        self,
        event: LimitChatHistoryEvent,
        agent_config: WikiAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> RetrieverEvent:
        """
        Retrieves relevant nodes from the knowledge base.
        """
        await displayer.display_thought(t("agent.thought.searching_knowledge"))
        embedding, _ = agent_config.retrieve_step_config.embed_model.to_llama_index()
        last_user_message = [msg for msg in event.limited_history if msg.role == MessageRole.USER][-1]
        vector_store = agent_config.retrieve_step_config.vector_store.to_llama_index()
        nodes = retrieve_nodes(
            message=last_user_message.content,
            retrieve_k=agent_config.retrieve_step_config.retrieve_k,
            embed_model=embedding,
            index_namespaces=agent_config.retrieve_step_config.index_namespaces,
            query_mode=agent_config.retrieve_step_config.query_mode,
            node_types=agent_config.retrieve_step_config.node_types,
            vector_store=vector_store,
        )
        return RetrieverEvent.from_nodes(nodes)

    @step(
        name=LocaleString(en="Context Sufficient Guard"),
        description=LocaleString(en="Guards the context to ensure it is sufficient for generating a response."),
    )
    async def not_zero_nodes_guard_step(
        self,
        displayer: EventDisplayer,
        event: RetrieverEvent,
    ) -> AtLeastOneNodeEvent | ZeroNodesEvent:
        if len(event.nodes) > 0:
            await displayer.display_thought("At Least one Source was found")
            return AtLeastOneNodeEvent()

        await displayer.display_thought("No Source found")
        return ZeroNodesEvent()

    @step(
        name=LocaleString(en="Respond with LLM"),
        description=LocaleString(en="Generates a response using the configured LLM."),
    )
    async def respond_with_llm_step(
        self,
        _: AtLeastOneNodeEvent,
        limited_history_event: LimitChatHistoryEvent,
        retriever_event: RetrieverEvent,
        agent_config: WikiAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> LLMStopEvent:

        system_messages = [msg for msg in limited_history_event.limited_history if msg.role == MessageRole.SYSTEM]
        non_system_messages = [msg for msg in limited_history_event.limited_history if msg.role != MessageRole.SYSTEM]

        context = ""
        for node in retriever_event.nodes:
            context += f"<item>\n{node.content}\n</item>\n"
        context += ""

        context_prompt_locale = t.extract(agent_config.context_prompt, t.locale)

        context_message = ChatMessage(
            role=MessageRole.SYSTEM,
            content=PromptTemplate(context_prompt_locale).format(context=context),
        )

        messages = system_messages + [context_message] + non_system_messages

        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(agent_config.llm, llm, messages, as_stop_step=True)

    @step(
        name=LocaleString(en="Respond when no Nodes"),
        description=LocaleString(en="Generates a response when no Nodes are found."),
    )
    async def respond_when_no_nodes(
        self,
        _: ZeroNodesEvent,
        event: UserMessageEvent,
        displayer: EventDisplayer,
    ) -> StopEvent:
        last_user_message = [msg for msg in event.messages if msg.role == MessageRole.USER][-1]
        response = f"No Context information found to Question: \n {last_user_message.content}"
        await displayer.display_chunk(response, "WikiAgent")
        return StopEvent()
