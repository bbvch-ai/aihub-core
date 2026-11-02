"""
Stops a blueprint hands to `Conversation.complete(stop=...)` travel inside the request's payload, where no
step's return type names them. Discovery builds the REST response model from `get_stop_events()`, so a stop
missing there reaches REST clients serialized as a bare `StopEvent`, without its answer or reason.
"""

import pytest
from swiss_ai_hub.core.events.agent import RAGFailureStopEvent, RAGSuccessStopEvent, RefusalStopEvent
from swiss_ai_hub.core.workflow.visualizers.workflow_visualizer import WorkflowVisualizer

from swiss_ai_hub.agent.agents.expert_rag_agent.expert_rag_agent import ExpertRAGAgent
from swiss_ai_hub.agent.agents.few_shot_agent.few_shot_agent import FewShotAgent
from swiss_ai_hub.agent.agents.rag_agent.rag_agent import RAGAgent

RAG_STOPS = {RAGSuccessStopEvent, RAGFailureStopEvent}


@pytest.mark.parametrize("blueprint", [RAGAgent, ExpertRAGAgent])
def test_rag_blueprints_report_the_stops_they_complete_with(blueprint):
    assert blueprint.get_stop_events() >= RAG_STOPS


def test_few_shot_reports_the_refusal_it_completes_with():
    assert RefusalStopEvent in FewShotAgent.get_stop_events()


@pytest.mark.parametrize("blueprint", [RAGAgent, ExpertRAGAgent])
def test_the_graph_ends_the_completion_step_in_the_rag_stops(blueprint):
    links = {(link.source, link.target) for link in WorkflowVisualizer(agent=blueprint).build().links}

    for stop in RAG_STOPS:
        assert ("complete_conversation_step", f"stop_{stop.__name__}") in links
