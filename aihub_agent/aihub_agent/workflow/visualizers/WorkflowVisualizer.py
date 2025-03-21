import inspect
import logging
from types import UnionType
from typing import Type, get_origin, get_args, Union
from collections import defaultdict

import networkx as nx

from aihub_agent.agents.abstract.Agent import Agent
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import ControlEvent, StartEvent, StopEvent

from aihub_agent.workflow.annotations.extractors.extract_return_events import extract_return_events

logger = logging.getLogger(__name__)


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

    def __init__(self, agent: Type[Agent], locale: str = "en"):
        """
        Initialize the WorkflowVisualizer with an agent class and locale.

        Args:
            agent: The agent class to visualize
            locale: The locale for text labels (default: "en")
        """
        self.agent = agent
        self.locale = locale
        self.graph = None

    def build_workflow_graph(self):
        """
        Build a directed graph representing the workflow of the given agent.
        Uses locale to determine the displayed node labels based on the given LocaleString.

        Returns:
            networkx.DiGraph: The workflow graph
        """
        G = nx.DiGraph()

        # Special nodes
        START_NODE = "Start"
        END_NODE = "End"

        # Add special nodes
        G.add_node(
            START_NODE,
            type="start",
            node_id="start",
            label=LocaleString(de="Start", en="Start", fr="Début", it="Inizio").in_locale(self.locale)
        )

        G.add_node(
            END_NODE,
            type="stop",
            node_id="end",
            label=LocaleString(de="Ende", en="End", fr="Fin", it="Fine").in_locale(self.locale)
        )

        # Get all steps using the Agent's helper method
        steps = self.agent.get_steps()
        step_names = {step.__name__: step for step in steps}

        # Add step nodes
        for step_name, step_method in step_names.items():
            step_name_localized = self._get_localized_step_name(step_method, step_name)
            step_description = self._get_localized_step_description(step_method)
            step_icon = getattr(step_method, "_step_icon", None)

            # Extract input and output event info
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
                stop_on_error=getattr(step_method, "_stop_on_error", True)
            )

        # Map events to their producers and consumers
        self._create_event_mappings(G, step_names, START_NODE, END_NODE)

        self.graph = G
        return G

    def _get_localized_step_name(self, step_method, default_name):
        """
        Get the localized name of a step.

        Args:
            step_method: The step method
            default_name: Default name to use if no localized name is available

        Returns:
            str: The localized step name or default name
        """
        step_name_locale_str = getattr(step_method, "_step_name", None)
        if step_name_locale_str and isinstance(step_name_locale_str, LocaleString):
            return LocaleHandler(self.locale).extract(step_name_locale_str) or default_name
        return default_name

    def _get_localized_step_description(self, step_method):
        """
        Get the localized description of a step.

        Args:
            step_method: The step method

        Returns:
            str: The localized step description or None
        """
        step_description_locale_str = getattr(step_method, "_step_description", None)
        return LocaleHandler(self.locale).extract(step_description_locale_str) if step_description_locale_str else None

    def _get_step_input_events(self, step_method):
        """
        Get information about the input events required by a step.

        Args:
            step_method: The step method

        Returns:
            dict: Dictionary mapping parameter names to event types
        """
        input_event_mapping = getattr(step_method, "_input_event_mapping", {})
        optional_map = getattr(step_method, "_parameter_optional_map", {})

        # Convert to a more readable format for visualization
        result = {}
        for param_name, event_types in input_event_mapping.items():
            is_optional = optional_map.get(param_name, False)
            result[param_name] = {
                "event_types": [self._get_event_info(et) for et in event_types],
                "optional": is_optional
            }
        return result

    def _get_step_output_events(self, step_method):
        """
        Get information about the output events produced by a step.

        Args:
            step_method: The step method

        Returns:
            list: List of event type information
        """
        output_events = extract_return_events(step_method)
        return [self._get_event_info(event_type) for event_type in output_events]

    def _get_event_info(self, event_class):
        """
        Get basic information about an event class.

        Args:
            event_class: The event class

        Returns:
            dict: Dictionary with basic event information
        """
        info = {
            "name": event_class.__name__,
            "full_name": f"{event_class.__module__}.{event_class.__name__}",
            "is_start_event": issubclass(event_class, StartEvent),
            "is_stop_event": issubclass(event_class, StopEvent),
        }

        # Try to add payload information
        try:
            payload_info = self._extract_event_payload_info(event_class)
            info["payload"] = payload_info
        except Exception as e:
            logger.warning(f"Failed to extract payload info for {event_class.__name__}: {str(e)}")
            info["payload"] = {}

        return info

    def _extract_event_payload_info(self, event_class: Type[ControlEvent]):
        """
        Extract payload information from an event class.

        Args:
            event_class: The event class to extract payload from

        Returns:
            dict: Dictionary containing payload field information
        """
        from aihub_agent.workflow.annotations.extractors.extract_event_types import extract_event_types

        payload_info = {}

        # Check if the class has annotations (Pydantic model fields)
        if hasattr(event_class, "__annotations__"):
            for field_name, field_type in event_class.__annotations__.items():
                # Skip private fields
                if field_name.startswith('_'):
                    continue

                # Get human-readable type description
                type_desc = self._get_human_readable_type(field_type)

                # Get field description if available from Pydantic model
                description = None
                if hasattr(event_class, "model_fields") and field_name in event_class.model_fields:
                    field = event_class.model_fields[field_name]
                    description = field.description if hasattr(field, "description") else None

                field_info = {
                    "type": type_desc,
                    "description": description
                }

                payload_info[field_name] = field_info

        return payload_info

    def _get_human_readable_type(self, type_annotation):
        """
        Create a human-readable string representation of a type annotation.

        Args:
            type_annotation: A type annotation (can be a complex typing construct)

        Returns:
            str: A human-readable representation of the type
        """
        from aihub_agent.workflow.annotations.extractors.extract_event_types import extract_event_types
        import typing

        # Handle primitive types directly
        if type_annotation in (str, int, float, bool, dict, list):
            return type_annotation.__name__

        # Get origin and args for complex types
        origin = get_origin(type_annotation)
        args = get_args(type_annotation)

        # Handle Optional types (Union with None)
        if origin is Union or origin is UnionType:
            if type(None) in args:
                # It's an Optional type
                non_none_args = [arg for arg in args if arg is not type(None)]
                if len(non_none_args) == 1:
                    # Simple Optional[X]
                    return self._get_human_readable_type(non_none_args[0])
                else:
                    # Union with multiple types and None
                    return " | ".join(self._get_human_readable_type(arg) for arg in non_none_args)
            else:
                # Regular Union without None
                return " | ".join(self._get_human_readable_type(arg) for arg in args)

        # Handle List types
        elif origin in (list, typing.List):
            if args:
                elem_type = args[0]
                return f"{self._get_human_readable_type(elem_type)}[]"
            return "List"

        # Handle Dict types
        elif origin in (dict, typing.Dict):
            if len(args) == 2:
                key_type, value_type = args
                return f"Dict[{self._get_human_readable_type(key_type)}, {self._get_human_readable_type(value_type)}]"
            return "Dict"

        # Handle classes
        elif inspect.isclass(type_annotation):
            # Check if it's a BaseEvent
            from aihub_lib.nats.events import BaseEvent
            if issubclass(type_annotation, BaseEvent):
                return type_annotation.__name__
            return type_annotation.__name__

        # Fallback for anything else
        return str(type_annotation)

    def _create_event_mappings(self, G, step_names, START_NODE, END_NODE):
        """
        Create direct step-to-step connections based on event flow.

        Args:
            G: The graph to add edges to
            step_names: Dictionary mapping step names to step methods
            START_NODE: The start node identifier
            END_NODE: The end node identifier
        """
        # Map events to their producers and consumers
        event_producers = defaultdict(set)  # event_type -> set of producing step names
        event_consumers = defaultdict(set)  # event_type -> set of consuming step names

        # Build the mappings
        for step_name, step_method in step_names.items():
            # Map events consumed by this step
            input_events = getattr(step_method, "_input_events", set())
            for event_type in input_events:
                if issubclass(event_type, ControlEvent):
                    event_consumers[event_type].add(step_name)

            # Map events produced by this step
            output_events = extract_return_events(step_method)
            for event_type in output_events:
                if issubclass(event_type, ControlEvent):
                    event_producers[event_type].add(step_name)

        # Process each event to create direct connections
        for event_type in set(event_producers.keys()) | set(event_consumers.keys()):
            is_start_event = issubclass(event_type, StartEvent)
            is_stop_event = issubclass(event_type, StopEvent)
            event_producers_for_type = event_producers[event_type]
            event_consumers_for_type = event_consumers[event_type]

            # Get event details
            try:
                event_payload = self._extract_event_payload_info(event_type)
            except Exception as e:
                logger.warning(f"Failed to extract payload info for {event_type.__name__}: {str(e)}")
                event_payload = {}

            # Handle start events (START_NODE -> consumer steps)
            if is_start_event:
                for consumer in event_consumers_for_type:
                    self._add_edge(
                        G,
                        START_NODE,
                        consumer,
                        event_type=event_type.__name__,
                        event_full_name=f"{event_type.__module__}.{event_type.__name__}",
                        is_start_event=True,
                        is_stop_event=False,
                        payload=event_payload
                    )

            # Handle stop events (producer steps -> END_NODE)
            elif is_stop_event:
                for producer in event_producers_for_type:
                    self._add_edge(
                        G,
                        producer,
                        END_NODE,
                        event_type=event_type.__name__,
                        event_full_name=f"{event_type.__module__}.{event_type.__name__}",
                        is_start_event=False,
                        is_stop_event=True,
                        payload=event_payload
                    )

            # Handle regular events (producer steps -> consumer steps)
            else:
                for producer in event_producers_for_type:
                    for consumer in event_consumers_for_type:
                        self._add_edge(
                            G,
                            producer,
                            consumer,
                            event_type=event_type.__name__,
                            event_full_name=f"{event_type.__module__}.{event_type.__name__}",
                            is_start_event=False,
                            is_stop_event=False,
                            payload=event_payload
                        )

    def _add_edge(self, G, source, target, **attributes):
        """
        Add an edge to the graph with the given attributes.
        Handle potential parallel edges between the same nodes.

        Args:
            G: The graph to add the edge to
            source: Source node
            target: Target node
            attributes: Edge attributes
        """
        # If there's already an edge between these nodes, make this a multi-edge
        if G.has_edge(source, target):
            # Get existing edges between these nodes
            existing_edges = [data for _, _, data in G.edges(data=True)
                              if _==source and target==target]

            # Add counter to edge ID to make it unique
            edge_id = len(existing_edges)
            G.add_edge(source, target, edge_id=edge_id, **attributes)
        else:
            # First edge between these nodes
            G.add_edge(source, target, edge_id=0, **attributes)

    def to_dict(self):
        """
        Convert the workflow graph to a JSON-serializable format.

        Returns:
            dict: A dictionary representation of the graph
        """
        if self.graph is None:
            self.build_workflow_graph()

        # Convert to a JSON-serializable format
        graph_data = {
            "directed": True,
            "multigraph": False,  # We're handling multi-edges ourselves with edge_id
            "graph": {},
            "nodes": [],
            "links": []
        }

        # Add nodes
        for node, attrs in self.graph.nodes(data=True):
            node_data = dict(attrs)
            node_data["id"] = node
            graph_data["nodes"].append(node_data)

        # Add edges
        for source, target, attrs in self.graph.edges(data=True):
            edge_data = dict(attrs)
            edge_data["source"] = source
            edge_data["target"] = target
            graph_data["links"].append(edge_data)

        return graph_data

    def visualize(self):
        """
        Visualize the workflow using networkx and matplotlib.
        """
        import matplotlib.pyplot as plt
        from matplotlib.patches import FancyArrowPatch
        import numpy as np

        if self.graph is None:
            self.build_workflow_graph()

        # Use a layout algorithm that works well for workflow graphs
        pos = nx.spring_layout(self.graph, seed=42, k=0.8)

        plt.figure(figsize=(14, 10))

        # Draw different node types with different styles
        step_nodes = [n for n, attrs in self.graph.nodes(data=True) if attrs.get('type') == 'step']
        special_nodes = [n for n, attrs in self.graph.nodes(data=True) if attrs.get('type') == 'special']

        # Draw step nodes
        nx.draw_networkx_nodes(
            self.graph, pos,
            nodelist=step_nodes,
            node_color="skyblue",
            node_size=2500,
            node_shape="s"  # square
        )

        # Draw special nodes (START/END)
        nx.draw_networkx_nodes(
            self.graph, pos,
            nodelist=special_nodes,
            node_color="lightgray",
            node_size=1500,
            node_shape="h"  # hexagon
        )

        # Add node labels
        node_labels = {}
        for node, data in self.graph.nodes(data=True):
            # For step nodes, use the label attribute or the step name
            node_labels[node] = data.get('label', node)

        nx.draw_networkx_labels(
            self.graph, pos,
            node_labels,
            font_size=9,
            font_family="sans-serif"
        )

        # Draw edges with custom positioning and labels
        for source, target, data in self.graph.edges(data=True):
            # Get positions
            source_pos = pos[source]
            target_pos = pos[target]

            # Draw the edge
            arrow = FancyArrowPatch(
                source_pos,
                target_pos,
                connectionstyle=f"arc3,rad=0.1",
                arrowstyle="->",
                mutation_scale=15,
                lw=1.5,
                color='gray'
            )
            plt.gca().add_patch(arrow)

            # Add edge label (event type)
            event_type = data.get('event_type', '')
            # Calculate midpoint with a small offset
            mid_x = (source_pos[0] + target_pos[0]) / 2
            mid_y = (source_pos[1] + target_pos[1]) / 2
            # Add a small offset to avoid overlap with the edge
            label_pos = (mid_x, mid_y + 0.03)

            plt.text(
                label_pos[0], label_pos[1],
                event_type,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8),
                ha='center', va='center',
                fontsize=8
            )

        plt.title(f"Workflow for {self.agent.__name__}", fontsize=16)
        plt.axis("off")
        plt.tight_layout()
        plt.show()