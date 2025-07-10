from aihub_lib.nats.events.form.base.FormkitElement import FormkitElement
from aihub_lib.nats.events.form.base.PrimeVueElement import PrimeVueElement
from aihub_lib.nats.events.work.WorkEvent import WorkEvent


class HumanWorkEvent(WorkEvent):
    """
    A work event that can be initiated by a human and may contain FormKit UI elements.
    """
    def to_formkit(self) -> list[FormkitElement]:
        """
        Generates a list of FormkitElement objects from the event's attributes.

        This method iterates over the model's fields and identifies attributes
        that are instances of FormkitElement. For elements that are subclasses
        of PrimeVueElement, it automatically assigns the attribute's key as the
        element's 'name'.
        """
        formkit_elements: list[FormkitElement] = []

        # Iterate over the fields of the Pydantic model instance
        for field_name, field_info in self.model_fields.items():
            field_value = getattr(self, field_name)

            # Check if the field's value is an instance of FormkitElement
            if isinstance(field_value, FormkitElement):
                # If it's a PrimeVueElement, it requires a 'name'
                if isinstance(field_value, PrimeVueElement):
                    # Create a copy to avoid mutating the original object
                    element_copy = field_value.model_copy()

                    # Set the name of the element to the field's name
                    element_copy.name = field_name
                    formkit_elements.append(element_copy)
                else:
                    # For other FormkitElements (e.g., HtmlElement), just append them
                    formkit_elements.append(field_value)

        return formkit_elements