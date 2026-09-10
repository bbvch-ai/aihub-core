from swiss_ai_hub.core.agents.visualizers.types.node_data import NodeData
from swiss_ai_hub.core.agents.visualizers.types.workflow_graph import WorkflowGraph


class WorkflowMermaidSerializer:
    """
    Renders a `WorkflowGraph` as a Mermaid `flowchart` so a reader (an LLM grounding a meta answer, or
    a Markdown renderer) sees the workflow's structure — gating, branches, ordering — instead of a flat
    list of step names.

    Node ids come straight from `NodeData.id` (step method names and `start_`/`stop_` prefixes), which are
    already valid Mermaid identifiers. Terminal nodes render as stadium shapes, steps as boxes.
    """

    def __init__(self, graph: WorkflowGraph) -> None:
        self.graph = graph

    def serialize(self) -> str:
        lines = ["flowchart TD"]
        lines.extend(f"    {self._render_node(node)}" for node in self.graph.nodes)
        lines.extend(f"    {link.source} --> {link.target}" for link in self.graph.links)
        return "\n".join(lines)

    def _render_node(self, node: NodeData) -> str:
        label = self._escape(node.label)
        if node.description is not None:
            label = f"{label}<br/>{self._escape(node.description)}"
        if node.type == "step":
            return f'{node.id}["{label}"]'
        return f'{node.id}(["{label}"])'

    @staticmethod
    def _escape(text: str) -> str:
        return text.replace('"', "'")
