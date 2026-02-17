from __future__ import annotations

import copy
import json
import logging
from functools import reduce
from types import UnionType
from typing import TYPE_CHECKING, Annotated, Any, ClassVar, Union, get_args, get_origin

from pydantic import BaseModel, ConfigDict, computed_field, create_model
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from aihub_lib.nats.events.form.base.FormkitElement import FormkitElement
from aihub_lib.nats.events.form.base.PrimeVueElement import PrimeVueElement

if TYPE_CHECKING:
    from aihub_lib.i18n.LocaleString import LocaleString

logger = logging.getLogger(__name__)


class Form(BaseModel):
    """
    Base class enabling duality between form definition and data model.

    The Form class allows a single Pydantic model to serve two purposes:
    1. **Form definition**: When instantiated with FormkitElement values, it defines what form to render
    2. **Data container**: When instantiated with primitive values, it holds validated submission data

    This duality ensures forms can never de-sync from their underlying data model.

    ## Basic Usage (Flat Fields)

    ```python
    class MyForm(Form):
        note: Annotated[str | InputText, Field(description="Enter a note")]
        terms: Annotated[bool | Checkbox, Field(description="Accept the terms")]

    # Form mode - for rendering:
    form = MyForm(note=InputText(label="Note"), terms=Checkbox(label="Terms"))
    elements = form.to_formkit_form()  # [InputText(name="note"), Checkbox(name="terms")]

    # Data mode - from submission:
    data = MyForm(note="Hello", terms=True)
    ```

    ## Nested Forms

    Forms can be nested. When a field value is itself a Form instance, `to_formkit_form()`
    recursively extracts its elements and wraps them in a Group:

    ```python
    class AddressForm(Form):
        street: Annotated[str | InputText, Field(...)]
        city: Annotated[str | InputText, Field(...)]

    class PersonForm(Form):
        name: Annotated[str | InputText, Field(...)]
        address: Annotated[AddressForm, Field(...)]  # Nested Form

    # Form mode:
    form = PersonForm(
        name=InputText(label="Name"),
        address=AddressForm(street=InputText(label="Street"), city=InputText(label="City")),
    )
    # to_formkit_form() produces:
    # [InputText(name="name"), Group(name="address", children=[InputText(name="street"), ...])]
    ```

    ## Array of Forms (Repeaters)

    When a field contains a list of Form instances, `to_formkit_form()` uses the first item
    as a template and wraps it in a Repeater:

    ```python
    class ExampleForm(Form):
        input: Annotated[str | InputText, Field(...)]
        valid: Annotated[bool | Checkbox, Field(...)]

    class ConfigForm(Form):
        examples: Annotated[list[ExampleForm], Field(...)]

    # Form mode - provide ONE template item:
    form = ConfigForm(
        examples=[ExampleForm(input=InputText(label="Input"), valid=Checkbox(label="Valid"))]
    )
    # to_formkit_form() produces:
    # [Repeater(name="examples", children=[InputText(name="input"), Checkbox(name="valid")])]
    ```
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    _form_registry: ClassVar[dict[str, type[Form]]] = {}

    @computed_field
    @property
    def _form_name(self) -> str:
        """The form type name, used for polymorphic deserialization."""
        return self.__class__.__name__

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        logger.debug(f"Registering Form {cls.__name__}")
        Form._form_registry[cls.__name__] = cls

    @classmethod
    def deserialize_form(cls, data: bytes | str | dict[str, Any]) -> Form:
        """Deserialize JSON data into the correct Form subclass based on _form_name."""
        if isinstance(data, dict):
            json_data = data.copy()
        elif isinstance(data, str):
            json_data = json.loads(data)
        elif isinstance(data, bytes):
            json_data = json.loads(data.decode())
        else:
            raise ValueError(f"Cannot deserialize data of type {type(data)}")

        form_name = json_data.get("_form_name")
        if form_name and isinstance(form_name, str):
            form_class = cls._form_registry.get(form_name)
            if form_class:
                return form_class.model_validate(json_data)

        # Fallback to base Form
        logger.warning(f"Form {form_name} not found in registry. Using fallback Form.")
        return Form.model_validate(json_data)

    def to_formkit_form(self, _id_prefix: str = "") -> list[FormkitElement]:
        """
        Recursively generates a list of FormkitElement objects from this form's fields.

        Handles:
        - **FormkitElement values**: Extracted directly, with name/id auto-assigned
        - **Nested Form values**: Recursively processed, wrapped in a Group
        - **List of Form values**: First item used as template, wrapped in a Repeater
        - **None values**: Skipped (optional fields not included in this form instance)

        Args:
            _id_prefix: Internal parameter for generating unique element IDs in nested forms.
                       Do not pass this manually - it's set automatically during recursion.

        Returns:
            List of FormkitElement objects ready for frontend rendering.
        """
        # Import here to avoid circular imports
        from aihub_lib.nats.events.form.elements.Group import Group
        from aihub_lib.nats.events.form.elements.Repeater import Repeater

        formkit_elements: list[FormkitElement] = []

        for field_name, field_info in self.__class__.model_fields.items():
            field_value = getattr(self, field_name)

            # Skip None values (optional fields not included in this form)
            if field_value is None:
                continue

            # Case 1: Direct FormkitElement value
            if isinstance(field_value, FormkitElement):
                element = self._prepare_formkit_element(field_value, field_name, field_info, _id_prefix)
                formkit_elements.append(element)

            # Case 2: Nested Form instance → recurse and wrap in Group
            elif isinstance(field_value, Form):
                nested_prefix = f"{_id_prefix}{field_name}."
                nested_elements = field_value.to_formkit_form(_id_prefix=nested_prefix)
                label = self._extract_label_from_field(field_info)
                group_condition = self._derive_group_condition(nested_elements)
                # Use prefixed ref for unique group ID (ref serializes as 'id' in JSON)
                group_ref = f"{_id_prefix}{field_name}" if _id_prefix else field_name
                group = Group(
                    name=field_name,
                    label=label,
                    children=nested_elements,
                    condition_if=group_condition,
                    ref=group_ref,
                )
                formkit_elements.append(group)

            # Case 3: List of Form instances → use first as template, wrap in Repeater
            elif isinstance(field_value, list) and len(field_value) > 0 and isinstance(field_value[0], Form):
                nested_prefix = f"{_id_prefix}{field_name}."
                template_elements = field_value[0].to_formkit_form(_id_prefix=nested_prefix)
                label = self._extract_label_from_field(field_info)
                # Use prefixed ref for unique repeater ID
                repeater_ref = f"{_id_prefix}{field_name}" if _id_prefix else field_name
                repeater = Repeater(
                    name=field_name,
                    label=label,
                    children=template_elements,
                    ref=repeater_ref,
                )
                formkit_elements.append(repeater)

            # Case 6: Primitive or non-Form value → skip (only FormkitElements go to form)
            # This happens when the field has a primitive value (data mode)

        return formkit_elements

    def _prepare_formkit_element(
        self,
        element: FormkitElement,
        field_name: str,
        field_info: FieldInfo,
        id_prefix: str = "",
    ) -> FormkitElement:
        """
        Prepares a FormkitElement for inclusion in the form output.

        For PrimeVueElement instances:
        - Auto-assigns the field name as the element's 'name'
        - Auto-assigns a unique 'id' using the prefix path (e.g., 'teams_config.channel_id')
        - Determines 'required' based on whether None is in the field's type union
        - Sets default value from Pydantic field if element has no explicit value
        """
        if isinstance(element, PrimeVueElement):
            element_copy = element.model_copy()
            element_copy.name = field_name
            if element_copy.ref is None:
                # Use prefixed path as ID to ensure uniqueness across nested forms
                # Note: 'ref' is the attribute, 'id' is its JSON alias
                element_copy.ref = f"{id_prefix}{field_name}"

            # Determine if field is required based on type annotation
            # Boolean elements (checkbox, toggle switch) are never required - unchecked = false is valid
            boolean_formkit_types = {"primeCheckbox", "primeToggleSwitch"}
            is_boolean_element = getattr(element_copy, "formkit", None) in boolean_formkit_types
            is_required = not is_boolean_element and not self._annotation_allows_none(field_info.annotation)
            element_copy.required = is_required

            # If element has no explicit value, use Pydantic field default
            if element_copy.value is None and field_info.default is not PydanticUndefined:
                # Only use primitive defaults (not FormkitElements or Forms)
                default = field_info.default
                if not isinstance(default, FormkitElement | Form) and default is not None:
                    element_copy.value = default

            return element_copy

        return element

    @staticmethod
    def _annotation_allows_none(annotation: Any) -> bool:
        """Check if a type annotation allows None (is Optional)."""
        origin = get_origin(annotation)

        if origin is Annotated:
            inner_type = get_args(annotation)[0]
            return Form._annotation_allows_none(inner_type)

        if origin in (Union, UnionType):
            union_args = get_args(annotation)
            return type(None) in union_args

        return False

    @staticmethod
    def _extract_label_from_field(field_info: FieldInfo) -> LocaleString | str | None:
        """
        Extract a label from field info, using title or description if available.

        This provides automatic labeling for nested Groups and Repeaters.
        """
        if field_info.title:
            return field_info.title
        if field_info.description:
            # Use first sentence of description as label if it's short
            desc = field_info.description
            if len(desc) <= 50:
                return desc
        return None

    @staticmethod
    def _derive_group_condition(children: list[FormkitElement]) -> str | None:
        """
        Derive a condition_if for a group based on its children's conditions.

        If all children have conditions, the group should only show when at least one child would show.
        This prevents empty groups from being displayed.

        Returns:
            - None if ANY child has no condition (at least one element always visible)
            - The single condition if all children have the same condition
            - OR-combined conditions if children have different conditions
        """
        conditions: set[str] = set()
        has_unconditional_child = False

        def collect_conditions(elements: list[FormkitElement]) -> None:
            nonlocal has_unconditional_child
            for element in elements:
                if element.condition_if:
                    conditions.add(element.condition_if)
                else:
                    # This element has no condition, so it's always visible
                    has_unconditional_child = True
                # Recursively check children of groups
                if hasattr(element, "children") and element.children:
                    collect_conditions(element.children)

        collect_conditions(children)

        # If any child is always visible, the group should be too
        if has_unconditional_child or not conditions:
            return None

        if len(conditions) == 1:
            return conditions.pop()

        # Multiple different conditions: combine with OR (show group if ANY child would show)
        # FormKit expression syntax: $: condition1 || condition2
        combined = " || ".join(sorted(conditions))
        return f"$: {combined}"

    @classmethod
    def to_form_submission_model(cls) -> type[BaseModel]:
        """
        Creates a Pydantic model suitable for validating form submissions.

        This method recursively processes the class's type annotations to:
        - Strip FormkitElement types from unions (keeping only primitives)
        - Convert nested Form types to their submission models
        - Convert list[Form] to list[submission model]

        Returns:
            A new Pydantic model class with FormkitElement types removed.
        """
        new_fields: dict[str, tuple[Any, FieldInfo]] = {}

        for field_name, field_info in cls.model_fields.items():
            annotation = field_info.annotation
            converted = cls._convert_annotation_for_submission(annotation, field_name)

            if converted is not None:
                new_fields[field_name] = (converted, copy.deepcopy(field_info))

        new_model_name = f"{cls.__name__}Submission"
        return create_model(new_model_name, **new_fields)

    @classmethod
    def _convert_annotation_for_submission(cls, annotation: Any, field_name: str = "") -> Any:
        """
        Recursively convert a type annotation for use in a submission model.

        - Strips FormkitElement types from unions
        - Converts Form types to their submission models
        - Handles list[Form] → list[submission model]
        - Warns on union of multiple Form types
        """
        origin = get_origin(annotation)

        if origin is Annotated:
            args = get_args(annotation)
            inner_type = args[0]
            converted_inner = cls._convert_annotation_for_submission(inner_type, field_name)
            if converted_inner is None:
                return None
            # Reconstruct Annotated with converted inner type
            return Annotated[tuple([converted_inner] + list(args[1:]))]  # type: ignore[return-value]

        if origin in (Union, UnionType):
            return cls._convert_union_for_submission(annotation, field_name)

        if origin is list:
            args = get_args(annotation)
            if args:
                item_type = args[0]
                converted_item = cls._convert_annotation_for_submission(item_type, field_name)
                if converted_item is not None:
                    return list[converted_item]
            return annotation

        if isinstance(annotation, type) and issubclass(annotation, Form) and annotation is not Form:
            return annotation.to_form_submission_model()

        # Primitive or other type - keep as is
        return annotation

    @classmethod
    def _convert_union_for_submission(cls, annotation: Any, field_name: str) -> Any:
        """Convert a Union type annotation for submission model."""
        union_args = get_args(annotation)

        # Warn if union contains multiple Form subclasses
        form_types = [arg for arg in union_args if isinstance(arg, type) and issubclass(arg, Form) and arg is not Form]
        if len(form_types) > 1:
            logger.warning(
                f"Field '{field_name}' has union of multiple Form types: {[t.__name__ for t in form_types]}. "
                f"At form creation time, developer should instantiate with a concrete type. "
                f"Pydantic will handle discrimination on submission."
            )

        converted_args: list[Any] = []
        for arg in union_args:
            # Keep None type
            if arg is type(None):
                converted_args.append(arg)
            # Skip FormkitElement types
            elif isinstance(arg, type) and issubclass(arg, FormkitElement):
                continue
            elif isinstance(arg, type) and issubclass(arg, Form) and arg is not Form:
                converted_args.append(arg.to_form_submission_model())
            # Keep other types as-is
            else:
                converted_args.append(arg)

        # Reconstruct union using | operator
        if len(converted_args) == 0:
            return None
        if len(converted_args) == 1:
            return converted_args[0]
        return reduce(lambda a, b: a | b, converted_args)

    # Type Introspection Helpers (Class Methods)

    @classmethod
    def _is_form_type(cls, annotation: Any) -> bool:
        """Check if annotation is or contains a Form subclass."""
        origin = get_origin(annotation)

        if origin is Annotated:
            return cls._is_form_type(get_args(annotation)[0])

        if origin in (Union, UnionType):
            return any(cls._is_form_type(arg) for arg in get_args(annotation))

        if isinstance(annotation, type) and issubclass(annotation, Form) and annotation is not Form:
            return True

        return False

    @classmethod
    def _is_form_list(cls, annotation: Any) -> bool:
        """Check if annotation is list[FormSubclass]."""
        origin = get_origin(annotation)

        if origin is Annotated:
            return cls._is_form_list(get_args(annotation)[0])

        if origin is list:
            args = get_args(annotation)
            if args:
                return cls._is_form_type(args[0])

        return False

    @classmethod
    def _contains_formkit_element(cls, annotation: Any) -> bool:
        """Check if annotation contains FormkitElement in a union."""
        origin = get_origin(annotation)

        if origin is Annotated:
            return cls._contains_formkit_element(get_args(annotation)[0])

        if origin in (Union, UnionType):
            return any(isinstance(arg, type) and issubclass(arg, FormkitElement) for arg in get_args(annotation))

        return False

    # Instance-based Methods for Configurable/Non-Configurable Separation

    def _is_configurable_value(self, value: Any) -> bool:
        """
        Check if a field value is configurable (contains FormKit elements).

        A value is configurable if:
        - It is a FormkitElement (including LocaleInput for LocaleString fields)
        - It is a Form instance with configurable values (recursive)
        - It is a list containing Form instances with configurable values
        """
        if isinstance(value, FormkitElement):
            return True

        if isinstance(value, Form):
            # Recursively check if nested Form has any configurable values
            return any(
                self._is_configurable_value(getattr(value, field_name))
                for field_name in value.__class__.model_fields
                if getattr(value, field_name, None) is not None
            )

        if isinstance(value, list) and len(value) > 0:
            first_item = value[0]
            if isinstance(first_item, Form):
                return self._is_configurable_value(first_item)

        return False

    def get_configurable_fields(self) -> set[str]:
        """
        Returns the set of field names that are configurable (have FormKit element values).

        These fields will be included in forms and expected in submissions.
        """
        configurable = set()
        for field_name in self.__class__.model_fields:
            value = getattr(self, field_name, None)
            if value is not None and self._is_configurable_value(value):
                configurable.add(field_name)
        return configurable

    def get_non_configurable_fields(self) -> set[str]:
        """
        Returns the set of field names that are non-configurable (have actual data values).

        These fields are NOT included in forms and NOT expected in submissions.
        They will be merged back in when processing StartEvent configs.
        """
        all_fields = set(self.__class__.model_fields.keys())
        return all_fields - self.get_configurable_fields()

    def get_non_configurable_values(self) -> dict[str, Any]:
        """
        Returns a dictionary of non-configurable field names to their values.

        These values will be merged with submission data to create a complete config.
        """
        non_configurable = {}
        for field_name in self.get_non_configurable_fields():
            value = getattr(self, field_name, None)
            if value is not None:
                if isinstance(value, BaseModel):
                    non_configurable[field_name] = value.model_dump()
                elif isinstance(value, list):
                    non_configurable[field_name] = [
                        item.model_dump() if isinstance(item, BaseModel) else item for item in value
                    ]
                else:
                    non_configurable[field_name] = value
        return non_configurable

    def to_template_data(self, form_config: Form) -> dict[str, Any]:
        """Extract configurable field values and identity fields for DB storage.

        Given a data-mode instance and the corresponding form-mode config,
        returns only the fields that should be persisted as a template.
        Non-configurable deployment-specific values (e.g. LLMConfig) are excluded
        because they are merged at runtime by the dispatcher via deep_merge().
        """
        configurable_fields = form_config.get_configurable_fields()
        full_dump = self.model_dump()
        identity_fields = {"agent_class", "agent_id", "process_class", "process_id", "name", "description", "icon"}
        return {k: v for k, v in full_dump.items() if k in configurable_fields or k in identity_fields}

    def to_configurable_submission_model(self) -> type[BaseModel]:
        """
        Creates a Pydantic model for validating form submissions based on instance values.

        Unlike `to_form_submission_model()` which is class-based (uses type annotations),
        this method is instance-based and only includes fields that have FormKit element
        values (configurable fields).

        Returns:
            A new Pydantic model class with only configurable fields.
        """
        new_fields: dict[str, tuple[Any, FieldInfo]] = {}
        configurable_fields = self.get_configurable_fields()

        for field_name, field_info in self.__class__.model_fields.items():
            if field_name not in configurable_fields:
                continue

            annotation = field_info.annotation
            converted = self._convert_annotation_for_submission(annotation, field_name)

            if converted is not None:
                new_fields[field_name] = (converted, copy.deepcopy(field_info))

        new_model_name = f"{self.__class__.__name__}ConfigurableSubmission"
        return create_model(new_model_name, **new_fields)

    @staticmethod
    def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """
        Deep merge two dictionaries, with override values taking precedence.

        This is used to merge non-configurable values from the form-mode config
        with configurable values from a form submission.
        """
        result = copy.deepcopy(base)

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = Form.deep_merge(result[key], value)
            elif key in result and isinstance(result[key], list) and isinstance(value, list):
                # For lists, replace entirely (form submissions replace list contents)
                result[key] = value
            else:
                result[key] = value

        return result
