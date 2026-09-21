from swiss_ai_hub.core.agents.visualizers.types.edge_data import EdgeData
from swiss_ai_hub.core.agents.visualizers.types.node_data import NodeData
from swiss_ai_hub.core.agents.visualizers.types.workflow_graph import WorkflowGraph
from swiss_ai_hub.core.workflow.visualizers.workflow_mermaid_serializer import WorkflowMermaidSerializer


def _graph() -> WorkflowGraph:
    return WorkflowGraph(
        nodes=[
            NodeData(id="start_UserMessageEvent", type="start", label="User Message"),
            NodeData(id="retrieve_step", type="step", label="Retrieve", description="Fetches documents"),
            NodeData(id="stop_StopEvent", type="stop", label="Stop"),
        ],
        links=[
            EdgeData(source="start_UserMessageEvent", target="retrieve_step"),
            EdgeData(source="retrieve_step", target="stop_StopEvent"),
        ],
    )


def test_serializes_a_mermaid_flowchart() -> None:
    mermaid = WorkflowMermaidSerializer(_graph()).serialize()

    assert mermaid.splitlines()[0] == "flowchart TD"
    assert "    start_UserMessageEvent --> retrieve_step" in mermaid
    assert "    retrieve_step --> stop_StopEvent" in mermaid


def test_steps_render_as_boxes_and_terminals_as_stadiums() -> None:
    mermaid = WorkflowMermaidSerializer(_graph()).serialize()

    assert '    retrieve_step["Retrieve<br/>Fetches documents"]' in mermaid
    assert '    start_UserMessageEvent(["User Message"])' in mermaid
    assert '    stop_StopEvent(["Stop"])' in mermaid


def test_double_quotes_in_labels_are_escaped() -> None:
    graph = WorkflowGraph(
        nodes=[NodeData(id="answer_step", type="step", label='Say "hi"')],
        links=[],
    )

    mermaid = WorkflowMermaidSerializer(graph).serialize()

    assert "    answer_step[\"Say 'hi'\"]" in mermaid
