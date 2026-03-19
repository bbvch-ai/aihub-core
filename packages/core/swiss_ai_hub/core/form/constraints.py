"""
Form-safe constraint validators for the duality pattern.

When using the duality pattern (e.g., `float | InputNumber`), standard Pydantic constraints
like `ge=0.0` or `min_length=1` fail because they can't be applied to form elements.

This module provides constraint validators that:
- Apply validation to primitive values (int, float, str, list, etc.)
- Skip validation for form elements (InputNumber, InputText, MultiSelect, etc.)

## Usage

Replace Pydantic Field constraints with these validators:

```python
# Before (fails with form elements):
temperature: Annotated[
    float | InputNumber,
    Field(ge=0.0, le=2.0),
] = 0.0

# After (works with both):
temperature: Annotated[
    float | InputNumber,
    Field(description="Temperature"),
    Ge(0.0),
    Le(2.0),
] = 0.0
```

## Available Constraints

- `Ge(min_val)` - Greater than or equal (>=)
- `Le(max_val)` - Less than or equal (<=)
- `Gt(min_val)` - Greater than (>)
- `Lt(max_val)` - Less than (<)
- `MinLen(min_length)` - Minimum length for strings/lists
- `MaxLen(max_length)` - Maximum length for strings/lists
- `Pattern(regex)` - Regex pattern for strings
"""

import re
from typing import Any

from pydantic import AfterValidator

from swiss_ai_hub.core.form.base.formkit_element import FormkitElement


def _is_form_element(v: Any) -> bool:
    """Check if value is a form element (should skip validation)."""
    return isinstance(v, FormkitElement)


def Ge(min_val: float | int):
    """Greater than or equal constraint. Skips validation for form elements."""

    def validator(v: Any) -> Any:
        if _is_form_element(v):
            return v
        if isinstance(v, int | float) and v < min_val:
            raise ValueError(f"Value must be >= {min_val}, got {v}")
        return v

    return AfterValidator(validator)


def Le(max_val: float | int):
    """Less than or equal constraint. Skips validation for form elements."""

    def validator(v: Any) -> Any:
        if _is_form_element(v):
            return v
        if isinstance(v, int | float) and v > max_val:
            raise ValueError(f"Value must be <= {max_val}, got {v}")
        return v

    return AfterValidator(validator)


def Gt(min_val: float | int):
    """Greater than constraint. Skips validation for form elements."""

    def validator(v: Any) -> Any:
        if _is_form_element(v):
            return v
        if isinstance(v, int | float) and v <= min_val:
            raise ValueError(f"Value must be > {min_val}, got {v}")
        return v

    return AfterValidator(validator)


def Lt(max_val: float | int):
    """Less than constraint. Skips validation for form elements."""

    def validator(v: Any) -> Any:
        if _is_form_element(v):
            return v
        if isinstance(v, int | float) and v >= max_val:
            raise ValueError(f"Value must be < {max_val}, got {v}")
        return v

    return AfterValidator(validator)


def MinLen(min_length: int):
    """Minimum length constraint for strings/lists. Skips validation for form elements."""

    def validator(v: Any) -> Any:
        if _is_form_element(v):
            return v
        if isinstance(v, str | list | tuple) and len(v) < min_length:
            raise ValueError(f"Length must be >= {min_length}, got {len(v)}")
        return v

    return AfterValidator(validator)


def MaxLen(max_length: int):
    """Maximum length constraint for strings/lists. Skips validation for form elements."""

    def validator(v: Any) -> Any:
        if _is_form_element(v):
            return v
        if isinstance(v, str | list | tuple) and len(v) > max_length:
            raise ValueError(f"Length must be <= {max_length}, got {len(v)}")
        return v

    return AfterValidator(validator)


def Pattern(regex: str):
    """Regex pattern constraint for strings. Skips validation for form elements."""
    compiled = re.compile(regex)

    def validator(v: Any) -> Any:
        if _is_form_element(v):
            return v
        if isinstance(v, str) and not compiled.match(v):
            raise ValueError(f"Value must match pattern '{regex}', got '{v}'")
        return v

    return AfterValidator(validator)
