import inspect
import logging
from collections import defaultdict
from types import UnionType
from typing import Any, TypeVar, Union, cast, get_args, get_origin

import networkx as nx
from swiss_ai_hub.agent.agents.Agent import Agent

from swiss_ai_hub.core.agents.visualizers.types.EdgeData import EdgeData
from swiss_ai_hub.core.agents.visualizers.types.EventInfo import EventInfo
from swiss_ai_hub.core.agents.visualizers.types.EventPayloadField import EventPayloadField
from swiss_ai_hub.core.agents.visualizers.types.InputEventInfo import InputEventInfo
from swiss_ai_hub.core.agents.visualizers.types.NodeData import NodeData
from swiss_ai_hub.core.agents.visualizers.types.WorkflowGraph import WorkflowGraph
from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler
from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events import BaseEvent, ControlEvent, StartEvent, StopEvent
from swiss_ai_hub.core.nats.workflow.annotations.extractors.extract_return_events import extract_return_events

logger = logging.getLogger(__name__)

T = TypeVar("T")
EventType = type[BaseEvent]


class WorkflowVisualizer:
    """
    Visualizes agent workflows using networkx.

    This class creates a directed graph representation of an agent's workflow by analyzing:
    - Step methods and their annotations
    - Input events required by each step
    - Output events produced by each step
    - Start and stop events that trigger workflow initiation and termination

    The graph includes special START and END nodes, with edges showing the event flow between steps.
    """

    def __init__(self, agent: type[Agent], locale: str = "en") -> None:
        """Initialize the WorkflowVisualizer with an agent class and locale."""
        self.agent = agent
        self.locale = locale
        self.graph: nx.DiGraph | None = None

    def build_workflow_graph(self) -> nx.DiGraph:
        """
        Build a directed graph representing the workflow of the given agent.
        Uses locale to determine the displayed node labels based on the given LocaleString.
        """
        G = nx.DiGraph()

        START_NODE = "Start"
        END_NODE = "End"

        G.add_node(
            START_NODE,
            type="start",
            node_id="start",
            label=LocaleString.from_i18n_path("lib.workflow.nodes.start").in_locale(self.locale),
        )

        G.add_node(
            END_NODE,
            type="stop",
            node_id="end",
            label=LocaleString.from_i18n_path("lib.workflow.nodes.end").in_locale(self.locale),
        )

        steps = self.agent.get_steps()
        step_names = {step.__name__: step for step in steps}

        for step_name, step_method in step_names.items():
            self._add_step_node(G, step_name, step_method)

        self._create_event_mappings(G, step_names, START_NODE, END_NODE)

        self.graph = G
        return G

    def _add_step_node(self, G: nx.DiGraph, step_name: str, step_method: Any) -> None:
        """Add a step node to the graph with all its attributes."""
        step_name_localized = self._get_localized_step_name(step_method, step_name)
        step_description = self._get_localized_step_description(step_method)
        step_icon = getattr(step_method, "_step_icon", None)

        input_events = self._get_step_input_events(step_method)
        output_events = self._get_step_output_events(step_method)

        G.add_node(
            step_name,
            type="step",
            node_id=f"step_{step_name}",
            label=step_name_localized,
            description=step_description,
            icon=step_icon,
            input_events=input_events,
            output_events=output_events,
            max_executions=getattr(step_method, "_max_executions_per_run", None),
            stop_on_error=getattr(step_method, "_stop_on_error", True),
        )

    def _get_localized_step_name(self, step_method: Any, default_name: str) -> str:
        """Get the localized name of a step."""
        step_name_locale_str = getattr(step_method, "_step_name", None)
        if step_name_locale_str and isinstance(step_name_locale_str, LocaleString):
            return LocaleHandler(self.locale).extract(step_name_locale_str) or default_name
        return default_name

    def _get_localized_step_description(self, step_method: Any) -> str | None:
        """Get the localized description of a step."""
        step_description_locale_str = getattr(step_method, "_step_description", None)
        return LocaleHandler(self.locale).extract(step_description_locale_str) if step_description_locale_str else None

    def _get_step_input_events(self, step_method: Any) -> dict[str, InputEventInfo]:
        """Get information about the input events required by a step."""
        input_event_mapping = getattr(step_method, "_input_event_mapping", {})
        optional_map = getattr(step_method, "_parameter_optional_map", {})

        result = {}
        for param_name, event_classes in input_event_mapping.items():
            is_optional = optional_map.get(param_name, False)

            event_info_list = [self._get_event_info(et) for et in event_classes]

            input_event_info = InputEventInfo(event_names=event_info_list, optional=is_optional)

            result[param_name] = input_event_info

        return result

    def _get_step_output_events(self, step_method: Any) -> list[EventInfo]:
        """Get information about the output events produced by a step."""
        output_events = extract_return_events(step_method)
        return [self._get_event_info(event_class) for event_class in output_events]

    def _get_event_info(self, event_class: EventType) -> EventInfo:
        """Get basic information about an event class."""
        try:
            payload_info = self._extract_event_payload_info(event_class)
        except Exception as e:
            logger.warning(f"Failed to extract payload info for {event_class.event_name_from_class()}: {str(e)}")
            payload_info = {}

        event_info = EventInfo(
            name=event_class.event_name_from_class(),
            full_name=f"{event_class.__module__}.{event_class.event_name_from_class()}",
            is_start_event=issubclass(event_class, StartEvent),
            is_stop_event=issubclass(event_class, StopEvent),
            payload=payload_info,
        )

        return event_info

    def _extract_event_payload_info(self, event_class: EventType) -> dict[str, EventPayloadField]:
        """Extract payload information from an event class."""
        payload_info = {}

        if not hasattr(event_class, "__annotations__"):
            return payload_info

        for field_name, field_type in event_class.__annotations__.items():
            if field_name.startswith("_"):
                continue

            type_desc = self._get_human_readable_type(field_type)
            description = None

            if hasattr(event_class, "model_fields") and field_name in event_class.model_fields:
                field = event_class.model_fields[field_name]
                description = field.description if hasattr(field, "description") else None

            payload_field = EventPayloadField(type=type_desc, description=description)

            payload_info[field_name] = payload_field

        return payload_info

    def _get_human_readable_type(self, type_annotation: Any) -> str:
        """Create a human-readable string representation of a type annotation."""
        if type_annotation in (str, int, float, bool, dict, list):
            return type_annotation.__name__

        origin = get_origin(type_annotation)
        args = get_args(type_annotation)

        if origin is Union or origin is UnionType:
            return self._format_union_type(args)
        if origin in (list, list) and args:
            return f"{self._get_human_readable_type(args[0])}[]"
        elif origin in (dict, dict) and len(args) == 2:
            key_type, value_type = args
            return f"dict[{self._get_human_readable_type(key_type)}, {self._get_human_readable_type(value_type)}]"
        elif inspect.isclass(type_annotation):
            if hasattr(BaseEvent, "__class__") and issubclass(type_annotation, BaseEvent):
                return type_annotation.__name__
            return type_annotation.__name__

        return str(type_annotation)

    def _format_union_type(self, args: tuple[Any, ...]) -> str:
        """Format a Union type for human readability."""
        if type(None) in args:
            non_none_args = [arg for arg in args if arg is not type(None)]
            if len(non_none_args) == 1:
                return f"Optional[{self._get_human_readable_type(non_none_args[0])}]"
            else:
                return " | ".join(self._get_human_readable_type(arg) for arg in non_none_args) + " | None"
        else:
            return " | ".join(self._get_human_readable_type(arg) for arg in args)

    def _create_event_mappings(self, G: nx.DiGraph, step_names: dict[str, Any], START_NODE: str, END_NODE: str) -> None:
        """Create direct step-to-step connections based on event flow."""
        event_producers: dict[EventType, set[str]] = defaultdict(set)
        event_consumers: dict[EventType, set[str]] = defaultdict(set)

        self._build_event_mappings(step_names, event_producers, event_consumers)
        self._add_event_edges(G, event_producers, event_consumers, START_NODE, END_NODE)

    def _build_event_mappings(
        self,
        step_names: dict[str, Any],
        event_producers: dict[EventType, set[str]],
        event_consumers: dict[EventType, set[str]],
    ) -> None:
        """Build mappings between events and their producers/consumers."""
        for step_name, step_method in step_names.items():
            input_event_mapping = getattr(step_method, "_input_event_mapping", {})
            for param_name, event_classes in input_event_mapping.items():
                for event_class in event_classes:
                    if issubclass(event_class, ControlEvent):
                        event_consumers[event_class].add(step_name)

            output_events = extract_return_events(step_method)
            for event_class in output_events:
                if issubclass(event_class, ControlEvent):
                    event_producers[event_class].add(step_name)

    def _add_event_edges(
        self,
        G: nx.DiGraph,
        event_producers: dict[EventType, set[str]],
        event_consumers: dict[EventType, set[str]],
        START_NODE: str,
        END_NODE: str,
    ) -> None:
        """Add edges to the graph based on event flow."""
        for event_class in set(event_producers.keys()) | set(event_consumers.keys()):
            is_start_event = issubclass(event_class, StartEvent)
            is_stop_event = issubclass(event_class, StopEvent)
            producers = event_producers[event_class]
            consumers = event_consumers.get(event_class, set())

            try:
                payload_fields = self._extract_event_payload_info(event_class)
            except Exception as e:
                logger.warning(f"Failed to extract payload info for {event_class.event_name_from_class()}: {str(e)}")
                payload_fields = {}

            edge_attrs = {
                "event_name": event_class.event_name_from_class(),
                "event_full_name": f"{event_class.__module__}.{event_class.event_name_from_class()}",
                "is_start_event": False,
                "is_stop_event": False,
                "payload": payload_fields,
            }

            if is_start_event:
                edge_attrs["is_start_event"] = True
                for consumer in consumers:
                    self._add_edge(G, START_NODE, consumer, **edge_attrs)
            elif is_stop_event:
                edge_attrs["is_stop_event"] = True
                for producer in producers:
                    self._add_edge(G, producer, END_NODE, **edge_attrs)
            else:
                for producer in producers:
                    for consumer in consumers:
                        self._add_edge(G, producer, consumer, **edge_attrs)

        self._add_in_the_loop_edges(G, event_producers, event_consumers)

    def _add_in_the_loop_edges(
        self,
        G: nx.DiGraph,
        event_producers: dict[EventType, set[str]],
        event_consumers: dict[EventType, set[str]],
    ) -> None:
        """
        Add special edges for request-response pairs in "in the loop" patterns.
        """
        request_events = {}
        response_events = {}

        for event_class, producers in event_producers.items():
            name = event_class.__name__
            if "Request" in name and "Response" not in name:
                request_events[name] = (event_class, producers)

        for event_class, consumers in event_consumers.items():
            name = event_class.__name__
            if "Response" in name and "Request" not in name:
                response_events[name] = (event_class, consumers)

        # Match request-response pairs using direct name transformation
        for req_name, (req_class, producers) in request_events.items():
            expected_resp_name = req_name.replace("Request", "Response")

            if expected_resp_name in response_events:
                resp_class, consumers = response_events[expected_resp_name]

                for producer in producers:
                    for consumer in consumers:
                        edge_attrs = {
                            "event_name": f"{req_name[: req_name.rfind('Request')]}",
                            "event_full_name": f"{req_class.__module__}.{req_name} → "
                            f"{resp_class.__module__}.{expected_resp_name}",
                            "is_start_event": False,
                            "is_stop_event": False,
                            "payload": {},
                        }
                        self._add_edge(G, producer, consumer, **edge_attrs)

    def _add_edge(self, G: nx.DiGraph, source: str, target: str, **attributes: Any) -> None:
        """
        Add an edge to the graph with the given attributes.
        Handle potential parallel edges between the same nodes.
        """
        # If there's already an edge between these nodes, make this a multi-edge
        if G.has_edge(source, target):
            existing_edges = [data for _, _, data in G.edges(data=True) if _ == source]

            edge_id = len(existing_edges)
            G.add_edge(source, target, edge_id=edge_id, **attributes)
        else:
            G.add_edge(source, target, edge_id=0, **attributes)

    def to_pydantic(self) -> WorkflowGraph:
        """
        Convert the workflow graph to a Pydantic model.
        """
        if self.graph is None:
            self.build_workflow_graph()

        graph = cast(nx.DiGraph, self.graph)  # We know it's not None at this point

        nodes = []
        for node, attrs in graph.nodes(data=True):
            node_attrs = dict(attrs)
            node_attrs["id"] = node

            if "input_events" in node_attrs and node_attrs["input_events"]:
                input_events = {}
                for param, event_data in node_attrs["input_events"].items():
                    if isinstance(event_data, InputEventInfo):
                        input_events[param] = event_data
                    else:
                        input_events[param] = InputEventInfo.model_validate(event_data)
                node_attrs["input_events"] = input_events

            if "output_events" in node_attrs and node_attrs["output_events"]:
                output_events = []
                for event_data in node_attrs["output_events"]:
                    if isinstance(event_data, EventInfo):
                        output_events.append(event_data)
                    else:
                        output_events.append(EventInfo.model_validate(event_data))
                node_attrs["output_events"] = output_events

            node_model = NodeData.model_validate(node_attrs)
            nodes.append(node_model)

        links = []
        for source, target, attrs in graph.edges(data=True):
            edge_attrs = dict(attrs)
            edge_attrs["source"] = source
            edge_attrs["target"] = target

            if "payload" in edge_attrs and edge_attrs["payload"]:
                payload = {}
                for field_name, field_data in edge_attrs["payload"].items():
                    if isinstance(field_data, EventPayloadField):
                        payload[field_name] = field_data
                    else:
                        payload[field_name] = EventPayloadField.model_validate(field_data)
                edge_attrs["payload"] = payload

            edge_model = EdgeData.model_validate(edge_attrs)
            links.append(edge_model)

        return WorkflowGraph(directed=True, multigraph=False, graph={}, nodes=nodes, links=links)
