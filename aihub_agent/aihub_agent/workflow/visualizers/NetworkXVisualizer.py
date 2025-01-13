import inspect

import networkx as nx
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import ControlEvent, StartEvent, StopEvent

from aihub_agent.workflow.annotations.extractors.extract_return_events import (
    extract_return_events,
)


def is_control_event(cls) -> bool:
    """Check if cls is a ControlEvent or inherits from it."""
    return inspect.isclass(cls) and issubclass(cls, ControlEvent)


def is_start_event(cls) -> bool:
    """Check if cls is a StartEvent or inherits from it."""
    return inspect.isclass(cls) and issubclass(cls, StartEvent)


def is_end_event(cls) -> bool:
    """Check if cls is an EndEvent or inherits from it."""
    return inspect.isclass(cls) and issubclass(cls, StopEvent)


class WorkflowVisualizer:
    def __init__(self, cls: type, locale: str = "en"):
        """
        Initialize the WorkflowVisualizer with a class and locale.
        """
        self.cls = cls
        self.locale = locale
        self.graph = None

    def build_workflow_graph(self):
        """
        Build a directed graph representing the workflow of the given class.
        Uses locale to determine the displayed node labels based on the given LocaleString.
        """
        G = nx.DiGraph()

        # Special nodes
        START_NODE = LocaleString(
            de="Start", en="Start", fr="Début", it="Inizio"
        ).in_locale(self.locale)
        END_NODE = LocaleString(de="Ende", en="End", fr="Fin", it="Fine").in_locale(
            self.locale
        )
        G.add_node(START_NODE)
        G.add_node(END_NODE)

        # Identify step methods
        steps = [
            (name, func)
            for name, func in inspect.getmembers(self.cls, predicate=inspect.isfunction)
            if getattr(func, "_is_step", False)
        ]

        # Add step nodes
        for step_name, func in steps:
            step_name_localized = self._get_localized_step_name(func, step_name)
            step_description = self._get_localized_step_description(func)
            G.add_node(
                step_name, label=step_name_localized, description=step_description
            )

        # Build mappings for event consumption and production
        event_consumers, step_outputs = self._map_events_to_steps(steps)

        # Create graph edges
        self._add_edges_from_start_node(G, steps, START_NODE)
        self._add_edges_to_end_node(G, step_outputs, END_NODE)
        self._add_edges_between_steps(G, event_consumers, step_outputs)

        self.graph = G
        return G

    def _get_localized_step_name(self, func, step_name):
        """
        Get the localized name of a step.
        """
        step_name_locale_str = getattr(func, "_step_name", None)
        if step_name_locale_str and isinstance(step_name_locale_str, LocaleString):
            return step_name_locale_str.in_locale(self.locale) or step_name
        return step_name

    def _get_localized_step_description(self, func):
        """
        Get the localized description of a step.
        """
        step_description_locale_str = getattr(func, "_step_description", None)
        return (
            step_description_locale_str.in_locale(self.locale)
            if step_description_locale_str
            else None
        )

    def _map_events_to_steps(self, steps):
        """
        Map events to the steps that consume and produce them.
        """
        event_consumers = {}
        step_outputs = {}

        for step_name, func in steps:
            input_mapping = getattr(func, "_input_event_mapping", {})
            for param, event_classes in input_mapping.items():
                for event_cls in event_classes:
                    if is_control_event(event_cls):
                        event_consumers.setdefault(event_cls, set()).add(step_name)

            output_events = extract_return_events(func)
            step_outputs[step_name] = {
                evt for evt in output_events if is_control_event(evt)
            }

        return event_consumers, step_outputs

    def _add_edges_from_start_node(self, G, steps, START_NODE):
        """
        Add edges from the Start node to steps consuming StartEvents.
        """
        for step_name, func in steps:
            input_mapping = getattr(func, "_input_event_mapping", {})
            if any(
                is_start_event(evt)
                for event_set in input_mapping.values()
                for evt in event_set
            ):
                G.add_edge(START_NODE, step_name)

    def _add_edges_to_end_node(self, G, step_outputs, END_NODE):
        """
        Add edges from steps producing EndEvents to the End node.
        """
        for step_name, events in step_outputs.items():
            if any(is_end_event(evt) for evt in events):
                G.add_edge(step_name, END_NODE)

    def _add_edges_between_steps(self, G, event_consumers, step_outputs):
        """
        Add edges between steps where one step's outputs are consumed by another.
        """
        for step_name, events in step_outputs.items():
            for evt in events:
                for consumer_step in event_consumers.get(evt, set()):
                    if consumer_step != step_name:
                        G.add_edge(step_name, consumer_step)

    def visualize(self):
        """
        Visualize the workflow using networkx and matplotlib.
        """
        import matplotlib.pyplot as plt

        if self.graph is None:
            self.build_workflow_graph()
        pos = nx.spring_layout(self.graph, seed=42)

        # Extract labels from node attributes
        labels = {
            node: data.get("label", node) for node, data in self.graph.nodes(data=True)
        }

        plt.figure(figsize=(12, 8))

        # Draw nodes
        nx.draw_networkx_nodes(
            self.graph, pos, node_color="lightblue", node_size=3000, node_shape="o"
        )

        # Draw edges with adjusted connection style
        nx.draw_networkx_edges(
            self.graph,
            pos,
            arrowstyle="-|>",
            arrowsize=15,
            node_size=3000,
            connectionstyle="arc3,rad=0.1",
        )

        # Add custom labels
        nx.draw_networkx_labels(
            self.graph, pos, labels, font_size=9, font_family="sans-serif"
        )

        # Turn off axis
        plt.axis("off")
        plt.show()
