from pydantic import TypeAdapter

from swiss_ai_hub.core.form.all_form_options import ALL_FORM_OPTIONS
from swiss_ai_hub.core.form.elements.secret_file_input import SecretFileInput
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class TestSecretFileInput:
    def test_the_announced_element_carries_the_picker_props_under_their_frontend_names(self):
        element = SecretFileInput(label=LocaleString(en="Key file"), accept=".json", max_size_bytes=4096)

        dumped = element.model_dump(by_alias=True)

        assert dumped["formkit"] == "secretFileInput"
        assert dumped["accept"] == ".json"
        assert dumped["maxSizeBytes"] == 4096

    def test_an_announced_element_is_read_back_as_a_secret_file_input(self):
        element = SecretFileInput(label="Key file", name="key_file", accept=".json")

        restored = TypeAdapter(ALL_FORM_OPTIONS).validate_python(element.model_dump(by_alias=True))

        assert isinstance(restored, SecretFileInput)
        assert restored.accept == ".json"
