import inspect
from typing import Dict, Set, Type, Tuple

import networkx as nx

from aihub_agent.agents.abstract.Agent import Agent
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import ControlEvent, StartEvent, StopEvent

from aihub_agent.workflow.annotations.extractors.extract_return_events import extract_return_events


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
        START_NODE = LocaleString(de="Start", en="Start", fr="Début", it="Inizio").in_locale(self.locale)
        END_NODE = LocaleString(de="Ende", en="End", fr="Fin", it="Fine").in_locale(self.locale)
        G.add_node(START_NODE)
        G.add_node(END_NODE)

        # Get all steps using the Agent's helper method
        steps = self.agent.get_steps()
        step_names = {step.__name__: step for step in steps}

        # Add step nodes
        for step_name, step_method in step_names.items():
            step_name_localized = self._get_localized_step_name(step_method, step_name)
            step_description = self._get_localized_step_description(step_method)
            G.add_node(step_name, label=step_name_localized, description=step_description)

        # Build mappings for event consumption and production
        event_consumers, step_outputs = self._map_events_to_steps(step_names)

        # Create graph edges
        self._add_edges_from_start_node(G, step_names, START_NODE)
        self._add_edges_to_end_node(G, step_outputs, END_NODE)
        self._add_edges_between_steps(G, event_consumers, step_outputs)

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
            return step_name_locale_str.in_locale(self.locale) or default_name
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
        return step_description_locale_str.in_locale(self.locale) if step_description_locale_str else None

    def _map_events_to_steps(self, step_names: Dict[str, callable]) -> Tuple[Dict[Type[ControlEvent], Set[str]], Dict[str, Set[Type[ControlEvent]]]]:
        """
        Map events to the steps that consume and produce them.
        
        Args:
            step_names: Dictionary mapping step names to step methods
            
        Returns:
            A tuple of:
            - event_consumers: Dict mapping event types to sets of step names that consume them
            - step_outputs: Dict mapping step names to sets of event types they produce
        """
        event_consumers = {}
        step_outputs = {}

        for step_name, step_method in step_names.items():
            # Use _input_events attribute directly if available (added by @step decorator)
            input_events = getattr(step_method, "_input_events", set())
            for event_cls in input_events:
                if issubclass(event_cls, ControlEvent):
                    event_consumers.setdefault(event_cls, set()).add(step_name)

            # Extract return events using the dedicated helper
            return_events = extract_return_events(step_method)
            step_outputs[step_name] = {evt for evt in return_events if issubclass(evt, ControlEvent)}

        return event_consumers, step_outputs

    def _add_edges_from_start_node(self, G, step_names, START_NODE):
        """
        Add edges from the Start node to steps consuming StartEvents.
        
        Args:
            G: networkx.DiGraph
            step_names: Dictionary mapping step names to step methods
            START_NODE: Start node label
        """
        # Use the agent's get_start_events helper
        start_events = self.agent.get_start_events()
        
        for step_name, step_method in step_names.items():
            input_events = getattr(step_method, "_input_events", set())
            if any(issubclass(evt, StartEvent) for evt in input_events):
                G.add_edge(START_NODE, step_name)

    def _add_edges_to_end_node(self, G, step_outputs, END_NODE):
        """
        Add edges from steps producing StopEvents to the End node.
        
        Args:
            G: networkx.DiGraph
            step_outputs: Dict mapping step names to sets of event types they produce
            END_NODE: End node label
        """
        for step_name, events in step_outputs.items():
            if any(issubclass(evt, StopEvent) for evt in events):
                G.add_edge(step_name, END_NODE)

    def _add_edges_between_steps(self, G, event_consumers, step_outputs):
        """
        Add edges between steps where one step's outputs are consumed by another.
        
        Args:
            G: networkx.DiGraph
            event_consumers: Dict mapping event types to sets of step names that consume them
            step_outputs: Dict mapping step names to sets of event types they produce
        """
        for source_step, output_events in step_outputs.items():
            for event_type in output_events:
                consumer_steps = event_consumers.get(event_type, set())
                for target_step in consumer_steps:
                    # Avoid self-loops
                    if source_step != target_step:
                        G.add_edge(source_step, target_step)

    def to_dict(self):
        """
        Convert the workflow graph to a JSON-serializable format.
        
        Returns:
            dict: A dictionary representation of the graph
        """
        if self.graph is None:
            self.build_workflow_graph()
        return nx.node_link_data(self.graph)

    def visualize(self):
        """
        Visualize the workflow using networkx and matplotlib.
        """
        import matplotlib.pyplot as plt

        if self.graph is None:
            self.build_workflow_graph()
        pos = nx.spring_layout(self.graph, seed=42)

        # Extract labels from node attributes
        labels = {node: data.get("label", node) for node, data in self.graph.nodes(data=True)}

        plt.figure(figsize=(12, 8))

        # Draw nodes
        nx.draw_networkx_nodes(self.graph, pos, node_color="lightblue", node_size=3000, node_shape="o")

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
        nx.draw_networkx_labels(self.graph, pos, labels, font_size=9, font_family="sans-serif")

        # Turn off axis
        plt.axis("off")
        plt.show()
