from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.events.process.work.work_event import WorkEvent
from swiss_ai_hub.core.form.form import Form


class HumanWorkEvent(WorkEvent, Form):
    """
    Marks a piece of work submitted by a human. As humans usually require a form in the frontend to submit their
    data, this event is a subclass of Form. Hence, on the work that the human should submit, we define how the form
    looks like that will - when filled out correctly - result in the desired data structure.

    Hence, a human work event has always a double role:
    - When created in the process, it is created with form elements that describe the expected data structure.
    - When sent back from the user through the API, it is an instance holding the corresponding primitive data itself

    Hence, when subclassing a HumanWorkEvent, you define define the structure of both the data and the form:

    ```python
    class MyWorkEvent(HumanWorkEvent):
        note: Annotated[str | InputText, Field(description="Enter a note")]
        terms: Annotated[bool | InputCheckboxElement, Field(description="Accept the terms")]
    ```

    When requesting the human input from within a process, you instanciate a work event with the forms filled in

    ```python
    @process_step()
    def my_step(self, ...) -> Annotated[MyWorkRequestEvent, Human.Out(...)]:
        return MyWorkRequestEvent(
            forms=[
                MyWorkEvent(note=InputTextField(label="Note"), terms=InputCheckboxField(label="Accept the terms"))
            ]
        )
    ```

    Note that this might seem a bit counter-intuitive: The process itself instanciated a MyWorkEvent?
    Well, yes! However, it does not provide the actual data, but only the form elements.

    Hence, when the MyWorkRequestEvent it sent to the user, the frontend knows what form to render. The MyWorkEvent
    itself is never actually submitted to the process, it is only contained within the work REQUEST event.

    Only when it is submitted by the user with the actual data, it is received by the process.
    received_my_work_event # MyWorkEvent(note="This is what the user inputted", terms=True)
    """

    submitted_by: Annotated[UserIdentity | None, Field(description="The user who submitted the form.")] = None
