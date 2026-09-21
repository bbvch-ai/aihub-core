from swiss_ai_hub.core.agents import WorkflowGraph
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.workflow import WorkflowMermaidSerializer, WorkflowVisualizer

from swiss_ai_hub.agent.agents.agent import Agent

SELF_AWARENESS_STEP_NAMES: frozenset[str] = frozenset({"detect_meta_question_step", "answer_meta_question_step"})


def summarize_workflow_for_meta_answer(agent_type: type[Agent], t: LocaleHandler) -> str:
    """
    A Mermaid flowchart of an agent's own workflow, used to ground meta answers.

    The self-awareness steps themselves are pruned so the agent describes its actual work, not the
    machinery that answers questions about it.
    """
    graph = WorkflowVisualizer(agent=agent_type, locale=t.locale).build()
    return WorkflowMermaidSerializer(_without_self_awareness_steps(graph)).serialize()


def _without_self_awareness_steps(graph: WorkflowGraph) -> WorkflowGraph:
    """Drop the self-awareness step nodes and any terminal node left dangling once they are gone."""
    links = [
        link
        for link in graph.links
        if link.source not in SELF_AWARENESS_STEP_NAMES and link.target not in SELF_AWARENESS_STEP_NAMES
    ]
    connected = {link.source for link in links} | {link.target for link in links}
    nodes = [
        node
        for node in graph.nodes
        if node.id not in SELF_AWARENESS_STEP_NAMES and (node.type == "step" or node.id in connected)
    ]
    return WorkflowGraph(nodes=nodes, links=links)
