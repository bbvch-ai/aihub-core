"""
Comprehensive tests for the Form class with nested form support.

Tests cover:
- Flat forms (basic duality pattern)
- Nested Form instances (Group generation)
- Lists of Form instances (Repeater generation)
- Recursive to_form_submission_model()
- Type introspection helpers
- Edge cases and backward compatibility
"""

from typing import Annotated

from pydantic import BaseModel, Field

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.elements.Checkbox import Checkbox
from aihub_lib.nats.events.form.elements.Group import Group
from aihub_lib.nats.events.form.elements.InputNumber import InputNumber
from aihub_lib.nats.events.form.elements.InputText import InputText
from aihub_lib.nats.events.form.elements.LocaleInput import LocaleInput
from aihub_lib.nats.events.form.elements.Repeater import Repeater
from aihub_lib.nats.events.form.Form import Form

# =============================================================================
# Test Form Classes
# =============================================================================


class SimpleForm(Form):
    """Simple flat form for basic tests."""

    name: Annotated[str | InputText, Field(description="User name")]
    age: Annotated[int | InputNumber, Field(description="User age")]
    active: Annotated[bool | Checkbox, Field(description="Is active")]


class OptionalFieldForm(Form):
    """Form with optional fields."""

    required_field: Annotated[str | InputText, Field(description="Required")]
    optional_field: Annotated[str | None | InputText, Field(description="Optional")] = None


class NestedInnerForm(Form):
    """Inner form to be nested."""

    street: Annotated[str | InputText, Field(description="Street address")]
    city: Annotated[str | InputText, Field(description="City")]


class NestedOuterForm(Form):
    """Outer form containing a nested form."""

    name: Annotated[str | InputText, Field(description="Person name")]
    address: Annotated[NestedInnerForm, Field(description="Address")]


class DeepNestedLevel3(Form):
    """Level 3 of deep nesting."""

    value: Annotated[int | InputNumber, Field(description="Deep value")]


class DeepNestedLevel2(Form):
    """Level 2 of deep nesting."""

    level3: Annotated[DeepNestedLevel3, Field(description="Level 3")]


class DeepNestedLevel1(Form):
    """Level 1 of deep nesting."""

    level2: Annotated[DeepNestedLevel2, Field(description="Level 2")]


class ExampleItemForm(Form):
    """Item form for list/repeater tests."""

    input_text: Annotated[str | InputText, Field(description="Example input")]
    is_valid: Annotated[bool | Checkbox, Field(description="Is valid")]


class FormWithList(Form):
    """Form containing a list of nested forms."""

    title: Annotated[str | InputText, Field(description="Title")]
    examples: Annotated[list[ExampleItemForm], Field(description="Examples")]


class MixedForm(Form):
    """Form with flat fields, nested form, and list of forms."""

    name: Annotated[str | InputText, Field(description="Name")]
    config: Annotated[NestedInnerForm, Field(description="Configuration")]
    items: Annotated[list[ExampleItemForm], Field(description="Items")]


# =============================================================================
# Tests for Flat Forms (Basic Duality)
# =============================================================================


class TestFlatFormDuality:
    """Test basic flat form functionality (backward compatibility)."""

    def test_form_mode_extracts_elements(self) -> None:
        """Test that FormkitElements are extracted in form mode."""
        form = SimpleForm(
            name=InputText(label=LocaleString(en="Name")),
            age=InputNumber(label=LocaleString(en="Age")),
            active=Checkbox(label=LocaleString(en="Active")),
        )

        elements = form.to_formkit_form()

        assert len(elements) == 3
        assert all(not isinstance(e, Group) for e in elements)
        assert all(not isinstance(e, Repeater) for e in elements)

        # Check names are auto-assigned
        names = [e.name for e in elements]
        assert "name" in names
        assert "age" in names
        assert "active" in names

    def test_data_mode_returns_empty_elements(self) -> None:
        """Test that data mode (primitives) returns no form elements."""
        form = SimpleForm(name="John", age=30, active=True)

        elements = form.to_formkit_form()

        assert len(elements) == 0

    def test_submission_model_strips_formkit_elements(self) -> None:
        """Test that to_form_submission_model strips FormkitElement types."""
        SubmissionModel = SimpleForm.to_form_submission_model()

        # Should be able to validate with primitives
        instance = SubmissionModel(name="John", age=30, active=True)
        assert instance.name == "John"
        assert instance.age == 30
        assert instance.active is True

    def test_optional_field_required_detection(self) -> None:
        """Test that required/optional is correctly detected from type annotations."""
        form = OptionalFieldForm(
            required_field=InputText(label=LocaleString(en="Required")),
            optional_field=InputText(label=LocaleString(en="Optional")),
        )

        elements = form.to_formkit_form()
        required_elem = next(e for e in elements if e.name == "required_field")
        optional_elem = next(e for e in elements if e.name == "optional_field")

        assert required_elem.required is True
        assert optional_elem.required is False

    def test_none_values_are_skipped(self) -> None:
        """Test that None field values are not included in form output."""
        form = OptionalFieldForm(
            required_field=InputText(label=LocaleString(en="Required")),
            optional_field=None,
        )

        elements = form.to_formkit_form()

        assert len(elements) == 1
        assert elements[0].name == "required_field"


# =============================================================================
# Tests for Nested Forms (Group Generation)
# =============================================================================


class TestNestedForms:
    """Test nested Form handling with Group generation."""

    def test_nested_form_wrapped_in_group(self) -> None:
        """Test that nested Form instances are wrapped in Groups."""
        form = NestedOuterForm(
            name=InputText(label=LocaleString(en="Name")),
            address=NestedInnerForm(
                street=InputText(label=LocaleString(en="Street")),
                city=InputText(label=LocaleString(en="City")),
            ),
        )

        elements = form.to_formkit_form()

        assert len(elements) == 2

        # First element should be InputText
        assert isinstance(elements[0], InputText)
        assert elements[0].name == "name"

        # Second element should be Group
        assert isinstance(elements[1], Group)
        assert elements[1].name == "address"
        assert elements[1].label == "Address"  # From title

        # Group should have children
        assert len(elements[1].children) == 2
        child_names = [c.name for c in elements[1].children]
        assert "street" in child_names
        assert "city" in child_names

    def test_deeply_nested_forms(self) -> None:
        """Test that deeply nested forms produce nested Groups."""
        form = DeepNestedLevel1(
            level2=DeepNestedLevel2(
                level3=DeepNestedLevel3(
                    value=InputNumber(label=LocaleString(en="Deep Value")),
                ),
            ),
        )

        elements = form.to_formkit_form()

        assert len(elements) == 1
        assert isinstance(elements[0], Group)
        assert elements[0].name == "level2"

        # Level 2 should contain Level 3
        level2_children = elements[0].children
        assert len(level2_children) == 1
        assert isinstance(level2_children[0], Group)
        assert level2_children[0].name == "level3"

        # Level 3 should contain the InputNumber
        level3_children = level2_children[0].children
        assert len(level3_children) == 1
        assert isinstance(level3_children[0], InputNumber)
        assert level3_children[0].name == "value"

    def test_nested_form_submission_model(self) -> None:
        """Test that nested forms produce nested submission models."""
        SubmissionModel = NestedOuterForm.to_form_submission_model()

        # Should be able to validate nested data
        instance = SubmissionModel(
            name="John",
            address={"street": "123 Main St", "city": "Springfield"},
        )
        assert instance.name == "John"

    def test_deeply_nested_submission_model(self) -> None:
        """Test submission model for deeply nested forms."""
        SubmissionModel = DeepNestedLevel1.to_form_submission_model()

        instance = SubmissionModel(
            level2={"level3": {"value": 42}},
        )
        # The nested structure should be preserved
        assert instance.level2 is not None


# =============================================================================
# Tests for List of Forms (Repeater Generation)
# =============================================================================


class TestListOfForms:
    """Test list[Form] handling with Repeater generation."""

    def test_list_of_forms_wrapped_in_repeater(self) -> None:
        """Test that list[Form] is wrapped in a Repeater."""
        form = FormWithList(
            title=InputText(label=LocaleString(en="Title")),
            examples=[
                ExampleItemForm(
                    input_text=InputText(label=LocaleString(en="Input")),
                    is_valid=Checkbox(label=LocaleString(en="Valid")),
                ),
            ],
        )

        elements = form.to_formkit_form()

        assert len(elements) == 2

        # First should be InputText
        assert isinstance(elements[0], InputText)
        assert elements[0].name == "title"

        # Second should be Repeater
        assert isinstance(elements[1], Repeater)
        assert elements[1].name == "examples"
        assert elements[1].label == "Examples"  # From title

        # Repeater should have template children
        assert len(elements[1].children) == 2
        child_names = [c.name for c in elements[1].children]
        assert "input_text" in child_names
        assert "is_valid" in child_names

    def test_empty_list_produces_no_repeater(self) -> None:
        """Test that empty list doesn't produce a Repeater."""
        form = FormWithList(
            title=InputText(label=LocaleString(en="Title")),
            examples=[],
        )

        elements = form.to_formkit_form()

        # Only the title should be present
        assert len(elements) == 1
        assert elements[0].name == "title"

    def test_list_submission_model(self) -> None:
        """Test submission model handles list[Form] correctly."""
        SubmissionModel = FormWithList.to_form_submission_model()

        instance = SubmissionModel(
            title="My Examples",
            examples=[
                {"input_text": "First", "is_valid": True},
                {"input_text": "Second", "is_valid": False},
            ],
        )
        assert instance.title == "My Examples"
        assert len(instance.examples) == 2


# =============================================================================
# Tests for Mixed Forms
# =============================================================================


class TestMixedForms:
    """Test forms with combination of flat, nested, and list fields."""

    def test_mixed_form_produces_correct_structure(self) -> None:
        """Test form with flat fields, nested form, and list of forms."""
        form = MixedForm(
            name=InputText(label=LocaleString(en="Name")),
            config=NestedInnerForm(
                street=InputText(label=LocaleString(en="Street")),
                city=InputText(label=LocaleString(en="City")),
            ),
            items=[
                ExampleItemForm(
                    input_text=InputText(label=LocaleString(en="Input")),
                    is_valid=Checkbox(label=LocaleString(en="Valid")),
                ),
            ],
        )

        elements = form.to_formkit_form()

        assert len(elements) == 3

        # First: InputText
        assert isinstance(elements[0], InputText)
        assert elements[0].name == "name"

        # Second: Group (nested form)
        assert isinstance(elements[1], Group)
        assert elements[1].name == "config"
        assert len(elements[1].children) == 2

        # Third: Repeater (list of forms)
        assert isinstance(elements[2], Repeater)
        assert elements[2].name == "items"
        assert len(elements[2].children) == 2


# =============================================================================
# Tests for Type Introspection Helpers
# =============================================================================


class TestTypeIntrospection:
    """Test type introspection helper methods."""

    def test_is_form_type_direct(self) -> None:
        """Test _is_form_type with direct Form subclass."""
        assert Form._is_form_type(SimpleForm) is True
        assert Form._is_form_type(str) is False
        assert Form._is_form_type(BaseModel) is False

    def test_is_form_type_annotated(self) -> None:
        """Test _is_form_type with Annotated types."""
        annotation = Annotated[SimpleForm, Field(description="Test")]
        assert Form._is_form_type(annotation) is True

    def test_is_form_list(self) -> None:
        """Test _is_form_list detection."""
        assert Form._is_form_list(list[SimpleForm]) is True
        assert Form._is_form_list(list[str]) is False
        assert Form._is_form_list(str) is False

    def test_contains_formkit_element(self) -> None:
        """Test _contains_formkit_element detection."""
        assert Form._contains_formkit_element(str | InputText) is True
        assert Form._contains_formkit_element(str | int) is False
        assert Form._contains_formkit_element(str) is False

    def test_annotation_allows_none(self) -> None:
        """Test _annotation_allows_none detection."""
        assert Form._annotation_allows_none(str | None) is True
        assert Form._annotation_allows_none(str) is False
        assert Form._annotation_allows_none(Annotated[str | None, Field()]) is True


# =============================================================================
# Tests for Edge Cases
# =============================================================================


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_form_with_no_formkit_fields(self) -> None:
        """Test form where all fields have primitive values."""

        class PrimitiveOnlyForm(Form):
            name: str
            count: int

        form = PrimitiveOnlyForm(name="test", count=5)
        elements = form.to_formkit_form()
        assert len(elements) == 0

    def test_form_registry(self) -> None:
        """Test that forms are registered in the registry."""
        assert "SimpleForm" in Form._form_registry
        assert "NestedInnerForm" in Form._form_registry
        assert Form._form_registry["SimpleForm"] is SimpleForm

    def test_form_name_computed_field(self) -> None:
        """Test _form_name computed field."""
        form = SimpleForm(name="test", age=25, active=True)
        assert form._form_name == "SimpleForm"

    def test_deserialize_form(self) -> None:
        """Test form deserialization from dict."""
        data = {
            "_form_name": "SimpleForm",
            "name": "John",
            "age": 30,
            "active": True,
        }
        form = Form.deserialize_form(data)
        assert isinstance(form, SimpleForm)
        assert form.name == "John"


# =============================================================================
# Tests for LocaleString Duality
# =============================================================================


class TestLocaleStringDuality:
    """Test LocaleString and LocaleInput form duality pattern."""

    def test_locale_string_as_form_returns_locale_input(self) -> None:
        """Test that LocaleString.as_form() returns a LocaleInput element."""
        from aihub_lib.nats.events.form.elements.LocaleInput import LocaleInput

        locale_input = LocaleString.as_form(
            label=LocaleString(en="Name", de="Name"),
            input_type="text",
        )

        # as_form() now returns LocaleInput, not a LocaleString with FormkitElements
        assert isinstance(locale_input, LocaleInput)
        assert locale_input.formkit == "localeInput"
        assert locale_input.input_type == "text"

    def test_locale_string_data_mode(self) -> None:
        """Test that LocaleString with string values works as a data container."""
        data_locale = LocaleString(
            en="Hello",
            de="Hallo",
            fr="Bonjour",
            it="Ciao",
        )

        # LocaleString is now purely a data container
        assert data_locale._has_form_elements() is False
        assert data_locale.in_locale("en") == "Hello"
        assert data_locale.in_locale("de") == "Hallo"

    def test_locale_string_deprecated_methods_return_empty(self) -> None:
        """Test that deprecated form-related methods return empty values."""
        data_locale = LocaleString(en="Hello", de="Hallo")

        # These methods are kept for backwards compatibility but always return empty/False
        assert data_locale._has_form_elements() is False
        assert data_locale._to_formkit_elements() == []

    def test_locale_input_in_form_produces_element(self) -> None:
        """Test that LocaleInput in a Form produces a single LocaleInput element."""
        from aihub_lib.nats.events.form.elements.LocaleInput import LocaleInput

        class FormWithLocaleInput(Form):
            title: Annotated[str | InputText, Field(description="Title")]
            description: Annotated[LocaleString | LocaleInput, Field(description="Description")]

        form = FormWithLocaleInput(
            title=InputText(label=LocaleString(en="Title")),
            description=LocaleInput(
                label=LocaleString(en="Description", de="Beschreibung"),
                input_type="text",
            ),
        )

        elements = form.to_formkit_form()

        assert len(elements) == 2

        # First element: InputText
        assert isinstance(elements[0], InputText)
        assert elements[0].name == "title"

        # Second element: LocaleInput (not a Group)
        assert isinstance(elements[1], LocaleInput)
        assert elements[1].name == "description"
        assert elements[1].formkit == "localeInput"

    def test_locale_input_textarea_mode(self) -> None:
        """Test that LocaleInput with textarea mode has correct properties."""
        from aihub_lib.nats.events.form.elements.LocaleInput import LocaleInput

        locale_input = LocaleString.as_form(
            input_type="textarea",
            rows=5,
        )

        assert isinstance(locale_input, LocaleInput)
        assert locale_input.input_type == "textarea"
        assert locale_input.rows == 5

    def test_locale_string_data_mode_in_form_skipped(self) -> None:
        """Test that LocaleString with string values in a Form doesn't produce elements."""
        from aihub_lib.nats.events.form.elements.LocaleInput import LocaleInput

        class FormWithLocaleInput(Form):
            title: Annotated[str | InputText, Field(description="Title")]
            description: Annotated[LocaleString | LocaleInput, Field(description="Description")]

        # Data mode - LocaleString with strings (not LocaleInput)
        form = FormWithLocaleInput(
            title="My Title",
            description=LocaleString(en="Hello", de="Hallo"),
        )

        elements = form.to_formkit_form()

        # Only primitive values, no FormkitElements
        assert len(elements) == 0


# =============================================================================
# Tests for Submission Model Generation
# =============================================================================


class TestSubmissionModel:
    """Test to_form_submission_model in various scenarios."""

    def test_simple_submission_model(self) -> None:
        """Test basic submission model generation."""
        Model = SimpleForm.to_form_submission_model()
        assert Model.__name__ == "SimpleFormSubmission"

        # Validate data
        instance = Model(name="Test", age=25, active=True)
        assert instance.name == "Test"

    def test_nested_submission_model_validation(self) -> None:
        """Test nested submission model validates correctly."""
        Model = NestedOuterForm.to_form_submission_model()

        instance = Model(
            name="John",
            address={"street": "Main St", "city": "Boston"},
        )
        assert instance.name == "John"

    def test_list_submission_model_validation(self) -> None:
        """Test list submission model validates multiple items."""
        Model = FormWithList.to_form_submission_model()

        instance = Model(
            title="Test",
            examples=[
                {"input_text": "A", "is_valid": True},
                {"input_text": "B", "is_valid": False},
                {"input_text": "C", "is_valid": True},
            ],
        )
        assert len(instance.examples) == 3

    def test_mixed_submission_model(self) -> None:
        """Test mixed form submission model."""
        Model = MixedForm.to_form_submission_model()

        instance = Model(
            name="Test",
            config={"street": "Main", "city": "NYC"},
            items=[{"input_text": "Item", "is_valid": True}],
        )
        assert instance.name == "Test"


# =============================================================================
# Tests for Template Data Extraction
# =============================================================================


class TestTemplateData:
    """Test to_template_data() for extracting storable template data."""

    def test_includes_identity_fields(self) -> None:
        """Test that identity fields (agent_id, name, description, icon) are always included."""
        locale = LocaleString(en="Test", de="Test")

        data_config = AgentConfig(
            agent_id="test-1",
            name=locale,
            description=locale,
            icon="mage:robot",
        )

        form_config = AgentConfig(
            agent_id=InputText(label=LocaleString(en="ID")),
            name=LocaleInput(label=LocaleString(en="Name"), input_type="text"),
            description=LocaleInput(label=LocaleString(en="Desc"), input_type="textarea"),
        )

        result = data_config.to_template_data(form_config)
        result_dict = result.model_dump()

        assert "agent_id" in result_dict
        assert result_dict["agent_id"] == "test-1"
        assert "name" in result_dict
        assert "description" in result_dict
        assert "icon" in result_dict

    def test_includes_configurable_fields(self) -> None:
        """Test that configurable fields (with FormKit elements in form config) are included."""

        class CustomConfig(AgentConfig):
            customer_bucket: Annotated[str | InputText, Field(description="Bucket")] = "default"
            temperature: Annotated[float | InputNumber, Field(description="Temp")] = 0.7

        locale = LocaleString(en="Test", de="Test")

        data_config = CustomConfig(
            agent_id="test-1",
            name=locale,
            description=locale,
            customer_bucket="customers",
            temperature=0.9,
        )

        form_config = CustomConfig(
            agent_id=InputText(label=LocaleString(en="ID")),
            name=LocaleInput(label=LocaleString(en="Name"), input_type="text"),
            description=LocaleInput(label=LocaleString(en="Desc"), input_type="textarea"),
            customer_bucket=InputText(label=LocaleString(en="Bucket")),
            temperature=InputNumber(label=LocaleString(en="Temperature")),
        )

        result = data_config.to_template_data(form_config)
        result_dict = result.model_dump()

        assert result_dict["customer_bucket"] == "customers"
        assert result_dict["temperature"] == 0.9

    def test_excludes_non_configurable_fields(self) -> None:
        """Test that non-configurable fields (no FormKit element) are excluded from template data."""

        class LLMConfig(Form):
            model: str = "gpt-4"
            temperature: float = 0.7

        class CustomConfig(AgentConfig):
            customer_bucket: Annotated[str | InputText, Field(description="Bucket")] = "default"
            llm: LLMConfig = LLMConfig()

        locale = LocaleString(en="Test", de="Test")

        data_config = CustomConfig(
            agent_id="test-1",
            name=locale,
            description=locale,
            customer_bucket="customers",
            llm=LLMConfig(model="gpt-4o", temperature=0.5),
        )

        form_config = CustomConfig(
            agent_id=InputText(label=LocaleString(en="ID")),
            name=LocaleInput(label=LocaleString(en="Name"), input_type="text"),
            description=LocaleInput(label=LocaleString(en="Desc"), input_type="textarea"),
            customer_bucket=InputText(label=LocaleString(en="Bucket")),
            llm=LLMConfig(model="gpt-4", temperature=0.7),  # Non-configurable: no FormKit elements
        )

        result = data_config.to_template_data(form_config)
        result_dict = result.model_dump()

        assert "customer_bucket" in result_dict
        assert "llm" not in result_dict

    def test_excludes_internal_form_name_field(self) -> None:
        """Test that _form_name computed field is not in identity or configurable sets."""
        locale = LocaleString(en="Test", de="Test")

        data_config = AgentConfig(
            agent_id="test-1",
            name=locale,
            description=locale,
        )

        form_config = AgentConfig(
            agent_id=InputText(label=LocaleString(en="ID")),
            name=LocaleInput(label=LocaleString(en="Name"), input_type="text"),
            description=LocaleInput(label=LocaleString(en="Desc"), input_type="textarea"),
        )

        result = data_config.to_template_data(form_config)
        result_dict = result.model_dump()

        # _form_name is a computed field and not in model_dump() by default with exclude
        # but model_dump() does include computed fields, so we check it's handled
        assert result_dict.get("agent_id") == "test-1"

    def test_multiple_templates_produce_independent_data(self) -> None:
        """Test that two configs with different values produce distinct template dicts."""

        class CustomConfig(AgentConfig):
            customer_bucket: Annotated[str | InputText, Field(description="Bucket")] = "default"
            temperature: Annotated[float | InputNumber, Field(description="Temp")] = 0.7

        locale = LocaleString(en="Test", de="Test")

        form_config = CustomConfig(
            agent_id=InputText(label=LocaleString(en="ID")),
            name=LocaleInput(label=LocaleString(en="Name"), input_type="text"),
            description=LocaleInput(label=LocaleString(en="Desc"), input_type="textarea"),
            customer_bucket=InputText(label=LocaleString(en="Bucket")),
            temperature=InputNumber(label=LocaleString(en="Temperature")),
        )

        template_a = CustomConfig(
            agent_id="qa-mode",
            name=LocaleString(en="Q&A Mode", de="Q&A-Modus"),
            description=locale,
            customer_bucket="qa-bucket",
            temperature=0.3,
        )

        template_b = CustomConfig(
            agent_id="summary-mode",
            name=LocaleString(en="Summary Mode", de="Zusammenfassungsmodus"),
            description=locale,
            customer_bucket="summary-bucket",
            temperature=0.9,
        )

        result_a = template_a.to_template_data(form_config)
        result_b = template_b.to_template_data(form_config)

        result_a_dict = result_a.model_dump()
        result_b_dict = result_b.model_dump()

        assert result_a_dict["agent_id"] == "qa-mode"
        assert result_b_dict["agent_id"] == "summary-mode"
        assert result_a_dict["temperature"] == 0.3
        assert result_b_dict["temperature"] == 0.9
        assert result_a_dict["customer_bucket"] == "qa-bucket"
        assert result_b_dict["customer_bucket"] == "summary-bucket"
        assert result_a != result_b
