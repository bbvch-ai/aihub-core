from typing import Any


def normalize_empty_objects_to_none(value: Any) -> Any:
    """
    Recursively convert empty dicts {} to None.

    FormKit sends empty dicts for disabled/unconfigured nested form fields,
    but the backend expects None for proper Pydantic validation.
    """
    if value is None:
        return None

    if isinstance(value, dict):
        if not value:
            return None
        return {k: normalize_empty_objects_to_none(v) for k, v in value.items()}

    if isinstance(value, list):
        return [normalize_empty_objects_to_none(item) for item in value]

    return value


def normalize_empty_locale_strings(value: Any) -> Any:
    """
    Recursively convert empty LocaleString dicts to None.

    FormKit locale inputs may submit dicts with only locale keys (de/en/fr/it)
    where all values are empty. These should be treated as None.
    """
    if value is None:
        return None

    if isinstance(value, dict):
        locale_keys = {"de", "en", "fr", "it"}
        if set(value.keys()).issubset(locale_keys):
            if not value or all(not val for val in value.values()):
                return None

        return {k: normalize_empty_locale_strings(v) for k, v in value.items()}

    if isinstance(value, list):
        return [normalize_empty_locale_strings(item) for item in value]

    return value


def transform_formkit_arrays(data: Any) -> Any:
    """
    Recursively transform FormKit-style dict arrays back to Python lists.

    FormKit stores arrays as dicts with sequential numeric string keys:
    {'0': {...}, '1': {...}} -> [{...}, {...}]

    To avoid false positives with legitimate dicts that have numeric string keys,
    we also verify that all values are dicts (FormKit arrays always contain objects).
    """
    if isinstance(data, dict):
        keys = list(data.keys())
        if keys and all(isinstance(k, str) and k.isdigit() for k in keys):
            sorted_keys = sorted(keys, key=int)
            if sorted_keys == [str(i) for i in range(len(keys))]:
                values = [data[k] for k in sorted_keys]
                if all(isinstance(v, dict) for v in values):
                    return [transform_formkit_arrays(data[k]) for k in sorted_keys]
        return {k: transform_formkit_arrays(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [transform_formkit_arrays(item) for item in data]
    else:
        return data
