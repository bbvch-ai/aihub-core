from collections import defaultdict
from typing import Any, Literal

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
TerminalKind = Literal["start", "stop"]


class WorkflowVisualizer:
    """
    Builds a `WorkflowGraph` from an agent's step methods and event annotations.

    Each node carries only what the UI needs: id, type, label, description, icon.
    Edges are plain source→target arrows. One start node is emitted per concrete
    start-event type and one stop node per concrete stop-event type, labeled with
    the event's display name.
    """

    DEFAULT_START_ICON = "mage:play-circle-fill"
    DEFAULT_STOP_ICON = "mage:stop-circle-fill"

    def __init__(self, agent: type[Agent], locale: str = "en") -> None:
        self.agent = agent
        self.locale = locale

    def build(self) -> WorkflowGraph:
        nodes: dict[str, NodeData] = {}
        edges: set[tuple[str, str]] = set()

        steps = {step.__name__: step for step in self.agent.get_steps()}
        for step_name, step_method in steps.items():
            nodes[step_name] = NodeData(
                id=step_name,
                type="step",
                label=self._locale(getattr(step_method, "_step_name", None)) or step_name,
                description=self._locale(getattr(step_method, "_step_description", None)),
                icon=getattr(step_method, "_step_icon", None),
            )

        producers, consumers = self._collect_producers_and_consumers(steps)

        # Iterate event classes in a stable order so the serialized graph is
        # deterministic across runs (avoids flaky tests and noisy API diffs).
        event_classes = sorted(
            set(producers) | set(consumers),
            key=lambda ec: (ec.__module__, ec.__qualname__),
        )
        for event_class in event_classes:
            event_producers = producers.get(event_class, set())
            event_consumers = consumers.get(event_class, set())

            if issubclass(event_class, StartEvent):
                if not event_consumers:
                    continue
                source_id = self._ensure_terminal_node(nodes, event_class, kind="start")
                for consumer in event_consumers:
                    edges.add((source_id, consumer))
            elif issubclass(event_class, StopEvent):
                if not event_producers:
                    continue
                target_id = self._ensure_terminal_node(nodes, event_class, kind="stop")
                for producer in event_producers:
                    edges.add((producer, target_id))
            else:
                for producer in event_producers:
                    for consumer in event_consumers:
                        edges.add((producer, consumer))

        # Request/response "in-the-loop" pairs: close the loop from the producer of
        # each *Request to the consumer of the matching *Response.
        self._add_in_the_loop_edges(edges, producers, consumers)

        return WorkflowGraph(
            nodes=sorted(nodes.values(), key=lambda n: n.id),
            links=sorted(
                (EdgeData(source=s, target=t) for s, t in edges),
                key=lambda e: (e.source, e.target),
            ),
        )

    def _ensure_terminal_node(self, nodes: dict[str, NodeData], event_class: EventType, kind: TerminalKind) -> str:
        node_id = f"{kind}_{event_class.__name__}"
        if node_id in nodes:
            return node_id
        nodes[node_id] = NodeData(
            id=node_id,
            type=kind,
            label=self._locale(getattr(event_class, "_display_name", None)) or event_class.__name__,
            description=self._locale(getattr(event_class, "_display_description", None)),
            icon=self.DEFAULT_START_ICON if kind == "start" else self.DEFAULT_STOP_ICON,
        )
        return node_id

    def _locale(self, value: Any) -> str | None:
        if not isinstance(value, LocaleString):
            return None
        return LocaleHandler(self.locale).extract(value)

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

    def _add_in_the_loop_edges(
        self,
        edges: set[tuple[str, str]],
        producers: dict[EventType, set[str]],
        consumers: dict[EventType, set[str]],
    ) -> None:
        request_events = {
            ec.__name__: ps
            for ec, ps in producers.items()
            if "Request" in ec.__name__ and "Response" not in ec.__name__
        }
        response_events = {
            ec.__name__: cs
            for ec, cs in consumers.items()
            if "Response" in ec.__name__ and "Request" not in ec.__name__
        }
        for req_name, req_producers in request_events.items():
            resp_consumers = response_events.get(req_name.replace("Request", "Response"))
            if not resp_consumers:
                continue
            for producer in req_producers:
                for consumer in resp_consumers:
                    edges.add((producer, consumer))
