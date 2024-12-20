
from lib_core.nats.events.control.start import StartEvent
from lib_core.nats.events.display.DisplayEvent import DisplayEvent


class UserMessageEvent(DisplayEvent, StartEvent):
    """
    A start event triggered directly by a user's message, bridging both display and control functionalities.

    ### Why UserMessageEvent?
    While `StartEvent` influences the workflow’s starting point and `DisplayEvent` represents user-facing
    output, a `UserMessageEvent` marks a workflow start initiated by a user’s input. This is common in chat
    interfaces, voice assistants, or interactive dashboards, where a user’s message serves as both:
    - A display event (since it may appear in the UI history).
    - A control event triggering workflow execution from a particular starting step.

    By inheriting from `DisplayEvent` and `StartEvent`:
    - It ensures the event is visible in the user interface, displaying the user’s message.
    - It also sets the workflow in motion, deciding how and where the system responds or which step
      of the workflow to begin with.

    ### Use Case
    In an agent workflow, you might have:
    - **UserMessageEvent**: Initiates the workflow at a certain step due to user input.
    - Another start event from an agent or a system event: Initiates the workflow at a different step
      or with different initial conditions.

    This flexible design allows mixing and matching start events to adapt how and when workflows
    are triggered, depending on the source of the event.
    """
    pass
