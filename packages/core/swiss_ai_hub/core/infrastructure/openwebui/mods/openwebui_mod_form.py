"""Convert mod defaults and optional field hints to the platform's existing form elements."""

import re
from typing import Any

from pydantic import TypeAdapter, ValidationError

from swiss_ai_hub.core.form.all_form_options import ALL_FORM_OPTIONS
from swiss_ai_hub.core.form.base.formkit_element import FormkitElement
from swiss_ai_hub.core.i18n.locale_string import LOCALES


class OpenWebuiModForm:
    _ELEMENT_ADAPTER = TypeAdapter(ALL_FORM_OPTIONS)
    # Mod settings have no secret storage or tenant-scoped picker APIs.
    _UNAVAILABLE_CONTROLS = {
        "agentSelector",
        "knowledgeCollectionSelector",
        "knowledgeDatabaseSelector",
        "modelSelect",
        "modelBoundNumber",
        "modelGatedCheckbox",
        "tenantSelect",
        "vectorStoreInput",
        "primePassword",
        "secretFileInput",
    }
    _LOCALE_KEYS = set(LOCALES)
    _FIELD_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")

    @classmethod
    def _infer(cls, value: Any) -> str | None:
        if isinstance(value, bool):
            return "primeToggleSwitch"
        if isinstance(value, int | float):
            return "primeInputNumber"
        if isinstance(value, str) or value is None:
            return "primeInputText"
        if isinstance(value, dict):
            if (
                value
                and value.keys() <= cls._LOCALE_KEYS
                and all(isinstance(v, str) or v is None for v in value.values())
            ):
                return "localeInput"
            return "group"
        if isinstance(value, list):
            if all(isinstance(item, str) for item in value):
                return "chipsInput"
            if all(isinstance(item, dict) for item in value):
                return "repeater"
        return None

    @classmethod
    def _definition(cls, name: str, value: Any, hints: dict[str, Any]) -> dict[str, Any] | None:
        hints = dict(hints)
        control_keys = [key for key in ("control", "$formkit", "formkit") if key in hints]
        if len(control_keys) > 1:
            raise ValueError(f"Field '{name}': specify the control once")
        if control_keys:
            control = hints.pop(control_keys[0])
        elif "options" in hints:
            control = "primeSelect"
        else:
            control = cls._infer(value)
        if control is None and not control_keys:
            return None
        if not isinstance(control, str):
            raise ValueError(f"Field '{name}': control must be a FormKit control name")
        if control in cls._UNAVAILABLE_CONTROLS:
            raise ValueError(f"Mod settings control '{control}' requires secrets or platform services")
        if any(key in hints for key in ("name", "id", "ref", "value", "is_formkit_element", "validation")):
            raise ValueError(f"Field '{name}': name, id, value and validation are derived by the form builder")
        if hints.get("optionsApiMode") or hints.get("options_api_mode"):
            raise ValueError("Mod settings choices must be supplied in the package")
        return {"formkit": control, "name": name, "label": name.replace("_", " ").capitalize(), **hints}

    @staticmethod
    def _children(name: str, children: Any) -> dict[str, dict[str, Any]]:
        if children is None:
            return {}
        if not isinstance(children, list):
            raise ValueError(f"Field '{name}': children must be a list of named field definitions")
        result = {}
        for child in children:
            if not isinstance(child, dict) or not isinstance(child.get("name"), str):
                raise ValueError(f"Field '{name}': each child needs a name")
            child = dict(child)
            child_name = child.pop("name")
            if child_name in result:
                raise ValueError(f"Duplicate child field: {child_name}")
            result[child_name] = child
        return result

    @classmethod
    def _validate(cls, name: str, definition: dict[str, Any]) -> FormkitElement:
        try:
            element = cls._ELEMENT_ADAPTER.validate_python(definition)
        except ValidationError as error:
            issue = error.errors(include_url=False)[0]
            if issue["type"] == "union_tag_invalid":
                detail = f"unknown control {definition['formkit']!r}"
            else:
                property_path = ".".join(str(part) for part in issue["loc"][1:])
                detail = f"{property_path}: {issue['msg']}" if property_path else issue["msg"]
            raise ValueError(f"Field {name!r}: {detail}") from error
        allowed = {key for key in type(element).model_fields}
        allowed.update(field.alias for field in type(element).model_fields.values() if field.alias)
        unknown = definition.keys() - allowed
        if unknown:
            raise ValueError(f"Field '{name}': unknown control properties: {', '.join(sorted(unknown))}")
        return element

    @classmethod
    def build(
        cls,
        defaults: dict[str, Any],
        fields: dict[str, dict[str, Any]],
        *,
        _depth: int = 0,
        _in_repeater: bool = False,
    ) -> list[FormkitElement]:
        if _depth > 12:
            raise ValueError("Mod settings forms may be nested at most 12 levels")
        result: list[FormkitElement] = []
        for name in dict.fromkeys([*defaults, *fields]):
            if not cls._FIELD_NAME_PATTERN.fullmatch(name) or name in {"slots", "constructor", "prototype"}:
                if name in fields:
                    raise ValueError(f"Invalid mod setting field name: {name}")
                continue
            value = defaults.get(name)
            definition = cls._definition(name, value, fields.get(name, {}))
            if definition is None:
                continue
            control = definition["formkit"]
            # The shared renderer cannot mount a repeater inside another repeater's row.
            if control == "repeater" and _in_repeater:
                if name in fields:
                    raise ValueError("Mod settings do not support repeaters inside repeater rows")
                continue
            if name in defaults and value is None:
                definition.setdefault("nullable", True)
            if control in {"group", "repeater"}:
                children = cls._children(name, definition.pop("children", None))
                child_defaults = value[0] if isinstance(value, list) and value else value
                definition["children"] = cls.build(
                    child_defaults if isinstance(child_defaults, dict) else {},
                    children,
                    _depth=_depth + 1,
                    _in_repeater=_in_repeater or control == "repeater",
                )
            elif value is not None and not isinstance(value, list | dict):
                # Complex defaults are carried separately from the platform's scalar element value.
                definition["value"] = value
            result.append(cls._validate(name, definition))
        return result
