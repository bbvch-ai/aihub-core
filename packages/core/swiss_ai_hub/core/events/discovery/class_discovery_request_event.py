from swiss_ai_hub.core.events.base_event import BaseEvent


class ClassDiscoveryRequestEvent(BaseEvent):
    """
    Represents a request event for discovery-related operations, such as retrieving metadata,
    capabilities, or configuration details about agents or the system as a whole.

    ### Why DiscoveryRequestEvent?
    In a dynamic environment, components often need to discover what other agents are available,
    which functionalities they provide, or how they are configured. A `DiscoveryRequestEvent`
    encapsulates such queries in a standardized form, making it easy for discovery services
    or components to listen for these requests and respond appropriately.

    ### Characteristics
    - **Purely Informational:** While important, `DiscoveryRequestEvent` typically does not
      influence the system’s control flow (like `ControlEvent`) nor is it meant for end-user
      display (like `DisplayEvent`).
    - **Decoupled Queries:** By broadcasting discovery requests as events, systems can
      evolve and scale without centralized registries. New agents can respond to these requests
      when they come online.

    By subclassing `BaseEvent`, `DiscoveryRequestEvent` benefits from automatic registration,
    ensuring it can be easily deserialized and processed by any interested subscriber.
    """

    pass
