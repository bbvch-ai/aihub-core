from collections import defaultdict
from typing import Any, cast

import networkx as nx
from swiss_ai_hub.agent.agents.agent import Agent

from swiss_ai_hub.core.agents.visualizers.types.edge_data import EdgeData
from swiss_ai_hub.core.agents.visualizers.types.node_data import NodeData
from swiss_ai_hub.core.agents.visualizers.types.workflow_graph import WorkflowGraph
from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent
from swiss_ai_hub.core.events.agent.control.start.start_event import StartEvent
from swiss_ai_hub.core.events.agent.control.stop.stop_event import StopEvent
from swiss_ai_hub.core.events.base_event import BaseEvent
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.workflow.annotations.extractors.extract_return_events import extract_return_events

EventType = type[BaseEvent]


class WorkflowVisualizer:
    """
    Builds a directed graph representation of an agent's workflow.

    Each node carries only the minimum needed for rendering: id, type, label, description, icon.
    Edges are plain source→target arrows. One start node is created per concrete start event type
    and one stop node per concrete stop event type, labeled with the event's display name.
    """

    DEFAULT_START_ICON = "mage:play-circle-fill"
    DEFAULT_STOP_ICON = "mage:stop-circle-fill"

    def __init__(self, agent: type[Agent], locale: str = "en") -> None:
        self.agent = agent
        self.locale = locale
        self.graph: nx.DiGraph | None = None

    def build_workflow_graph(self) -> nx.DiGraph:
        G = nx.DiGraph()

        steps = {step.__name__: step for step in self.agent.get_steps()}
        for step_name, step_method in steps.items():
            self._add_step_node(G, step_name, step_method)

        producers, consumers = self._collect_producers_and_consumers(steps)
        self._add_edges(G, producers, consumers)
        self._add_in_the_loop_edges(G, producers, consumers)

        self.graph = G
        return G

    def _add_step_node(self, G: nx.DiGraph, step_name: str, step_method: Any) -> None:
        G.add_node(
            step_name,
            type="step",
            label=self._extract_locale(getattr(step_method, "_step_name", None)) or step_name,
            description=self._extract_locale(getattr(step_method, "_step_description", None)),
            icon=getattr(step_method, "_step_icon", None),
        )

    def _add_terminal_node(self, G: nx.DiGraph, event_class: EventType, kind: str) -> str:
        node_id = f"{kind}_{event_class.__name__}"
        if node_id in G.nodes:
            return node_id
        G.add_node(
            node_id,
            type=kind,
            label=self._extract_locale(getattr(event_class, "_display_name", None)) or event_class.__name__,
            description=self._extract_locale(getattr(event_class, "_display_description", None)),
            icon=self.DEFAULT_START_ICON if kind == "start" else self.DEFAULT_STOP_ICON,
        )
        return node_id

    def _extract_locale(self, locale_str: Any) -> str | None:
        if not isinstance(locale_str, LocaleString):
            return None
        return LocaleHandler(self.locale).extract(locale_str)

    def _collect_producers_and_consumers(
        self, steps: dict[str, Any]
    ) -> tuple[dict[EventType, set[str]], dict[EventType, set[str]]]:
        producers: dict[EventType, set[str]] = defaultdict(set)
        consumers: dict[EventType, set[str]] = defaultdict(set)
        for step_name, step_method in steps.items():
            for event_classes in getattr(step_method, "_input_event_mapping", {}).values():
                for event_class in event_classes:
                    if issubclass(event_class, ControlEvent):
                        consumers[event_class].add(step_name)
            for event_class in extract_return_events(step_method):
                if issubclass(event_class, ControlEvent):
                    producers[event_class].add(step_name)
        return producers, consumers

    def _add_edges(
        self,
        G: nx.DiGraph,
        producers: dict[EventType, set[str]],
        consumers: dict[EventType, set[str]],
    ) -> None:
        for event_class in set(producers) | set(consumers):
            event_producers = producers.get(event_class, set())
            event_consumers = consumers.get(event_class, set())

            if issubclass(event_class, StartEvent):
                if not event_consumers:
                    continue
                source = self._add_terminal_node(G, event_class, kind="start")
                for consumer in event_consumers:
                    G.add_edge(source, consumer)
            elif issubclass(event_class, StopEvent):
                if not event_producers:
                    continue
                target = self._add_terminal_node(G, event_class, kind="stop")
                for producer in event_producers:
                    G.add_edge(producer, target)
            else:
                for producer in event_producers:
                    for consumer in event_consumers:
                        G.add_edge(producer, consumer)

    def _add_in_the_loop_edges(
        self,
        G: nx.DiGraph,
        producers: dict[EventType, set[str]],
        consumers: dict[EventType, set[str]],
    ) -> None:
        """Pair Request producers with matching Response consumers so the graph closes the loop."""
        request_events = {
            ec.__name__: (ec, ps)
            for ec, ps in producers.items()
            if "Request" in ec.__name__ and "Response" not in ec.__name__
        }
        response_events = {
            ec.__name__: (ec, cs)
            for ec, cs in consumers.items()
            if "Response" in ec.__name__ and "Request" not in ec.__name__
        }

        for req_name, (_, req_producers) in request_events.items():
            resp_match = response_events.get(req_name.replace("Request", "Response"))
            if not resp_match:
                continue
            _, resp_consumers = resp_match
            for producer in req_producers:
                for consumer in resp_consumers:
                    G.add_edge(producer, consumer)

    def to_pydantic(self) -> WorkflowGraph:
        if self.graph is None:
            self.build_workflow_graph()
        graph = cast(nx.DiGraph, self.graph)

        nodes = [
            NodeData(id=node, **{k: v for k, v in attrs.items() if v is not None})
            for node, attrs in graph.nodes(data=True)
        ]
        links = [EdgeData(source=source, target=target) for source, target in graph.edges()]
        return WorkflowGraph(directed=True, multigraph=False, graph={}, nodes=nodes, links=links)
