"""Memory operations use the condensed standalone question, never the RAG-augmented prompt (#1753).

Chat clients running full-context RAG inline whole documents into the last user message. These tests pin
the two structural guarantees: the memory steps are wired downstream of the condenser (search embeds the
question, not documents), and the storage payload is the condensed question plus the answer (fact
extraction never sees the USER-role RAG context or the augmented message).
"""

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import (
    LimitChatHistoryEvent,
    LLMEvent,
    StandaloneQuestionCondenserEvent,
)
from swiss_ai_hub.core.events.agent.semantic.llm.message import Message

from swiss_ai_hub.agent.agents.expert_rag_agent.expert_rag_agent import ExpertRAGAgent
from swiss_ai_hub.agent.agents.rag_agent.rag_agent import RAGAgent
from swiss_ai_hub.agent.rag.step_functions import build_memory_conversation

AUGMENTED_USER_MESSAGE = "<context>whole inlined document text</context>\n<user_query>real question</user_query>"
RAG_CONTEXT_MESSAGE = "<REFERENCE_DOCUMENT>retrieved chunk</REFERENCE_DOCUMENT>"
CONDENSED_QUESTION = "What is the vacation policy?"
ANSWER = "You get 25 days."


def _steps_waiting_for(agent_class: type, event_class: type) -> set[str]:
    return {step.__name__ for step in agent_class.get_steps_waiting_for_event(event_class)}


def test_memory_retrieval_is_wired_off_the_condenser_in_both_agents():
    for agent_class in (RAGAgent, ExpertRAGAgent):
        on_condensed = _steps_waiting_for(agent_class, StandaloneQuestionCondenserEvent)
        assert {"retrieve_user_memory_step", "retrieve_organization_memory_step"} <= on_condensed
        assert "add_memory_to_chat_history_step" in _steps_waiting_for(agent_class, LimitChatHistoryEvent)


def test_memory_storage_is_wired_off_the_condenser_in_both_agents():
    for agent_class in (RAGAgent, ExpertRAGAgent):
        assert "store_user_memory_step" in _steps_waiting_for(agent_class, StandaloneQuestionCondenserEvent)


def test_build_memory_conversation_carries_only_the_condensed_question_and_the_answer():
    condense_event = StandaloneQuestionCondenserEvent(
        condensed_chat_message=ChatMessage(role=MessageRole.USER, content=CONDENSED_QUESTION)
    )
    llm_event = LLMEvent(
        input_messages=[
            Message.from_string(role="system", content="system prompt"),
            Message.from_string(role="user", content=RAG_CONTEXT_MESSAGE),
            Message.from_string(role="user", content=AUGMENTED_USER_MESSAGE),
        ],
        output_messages=[Message.from_string(role="assistant", content=ANSWER)],
    )

    conversation = build_memory_conversation(condense_event, llm_event)

    assert [message.content for message in conversation] == [CONDENSED_QUESTION, ANSWER]
    assert [message.role for message in conversation] == [MessageRole.USER, MessageRole.ASSISTANT]


def test_build_memory_conversation_without_answer_still_yields_the_question():
    condense_event = StandaloneQuestionCondenserEvent(
        condensed_chat_message=ChatMessage(role=MessageRole.USER, content=CONDENSED_QUESTION)
    )
    llm_event = LLMEvent(input_messages=[], output_messages=None)

    conversation = build_memory_conversation(condense_event, llm_event)

    assert [message.content for message in conversation] == [CONDENSED_QUESTION]
