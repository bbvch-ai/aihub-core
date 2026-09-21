from typing import Any

from fastapi import HTTPException
from pydantic import TypeAdapter
from swiss_ai_hub.core.auth import AccessChecker, KeycloakAdminService, UserIdentity
from swiss_ai_hub.core.form import ALL_FORM_OPTIONS, ConfigAuthorizationViolation, FormkitElement, Group, Repeater
from swiss_ai_hub.core.i18n import LocaleHandler


class ConfigAuthorizationService:
    """Validates that config values reference only resources the user is authorized to access."""

    _form_elements_adapter = TypeAdapter(list[ALL_FORM_OPTIONS])

    @staticmethod
    async def validate_for_user_or_raise(
        form_elements: list[dict],
        config: dict[str, Any],
        user: UserIdentity,
        t: LocaleHandler,
    ) -> None:
        accessible_tenant_ids = await KeycloakAdminService.get_user_tenant_ids(user.id)

        ConfigAuthorizationService.validate_config_authorization_or_raise(
            form_elements=form_elements,
            config=config,
            access_checker=AccessChecker.from_user(user),
            accessible_tenant_ids=accessible_tenant_ids,
            t=t,
        )

    @staticmethod
    def validate_config_authorization_or_raise(
        form_elements: list[dict],
        config: dict[str, Any],
        access_checker: AccessChecker,
        accessible_tenant_ids: set[str],
        t: LocaleHandler,
    ) -> None:
        """Validate config authorization and raise HTTP 403 if any violations are found."""

        typed_elements = ConfigAuthorizationService._form_elements_adapter.validate_python(form_elements)
        violations = ConfigAuthorizationService._validate_elements(
            typed_elements, config, access_checker, accessible_tenant_ids, t, prefix=""
        )
        if violations:
            raise HTTPException(
                status_code=403,
                detail={
                    "message": t("lib.common.authorization.config_unauthorized"),
                    "violations": [v.model_dump() for v in violations],
                },
            )

    @staticmethod
    def _validate_elements(
        elements: list[FormkitElement],
        config: dict[str, Any],
        access_checker: AccessChecker,
        accessible_tenant_ids: set[str],
        t: LocaleHandler,
        prefix: str,
    ) -> list[ConfigAuthorizationViolation]:
        """Walk typed form elements and validate authorization for each."""
        violations: list[ConfigAuthorizationViolation] = []

        for element in elements:
            name = getattr(element, "name", None)
            if not name:
                continue

            field_path = f"{prefix}{name}" if prefix else name

            if isinstance(element, Group):
                nested_config = config.get(name)
                violations.extend(
                    element.validate_authorization(field_path, nested_config, access_checker, accessible_tenant_ids, t)
                )
                if isinstance(nested_config, dict):
                    violations.extend(
                        ConfigAuthorizationService._validate_elements(
                            element.children,
                            nested_config,
                            access_checker,
                            accessible_tenant_ids,
                            t,
                            prefix=f"{field_path}.",
                        )
                    )

            elif isinstance(element, Repeater):
                items = config.get(name)
                if isinstance(items, list):
                    for i, item in enumerate(items):
                        if isinstance(item, dict):
                            violations.extend(
                                ConfigAuthorizationService._validate_elements(
                                    element.children,
                                    item,
                                    access_checker,
                                    accessible_tenant_ids,
                                    t,
                                    prefix=f"{field_path}.{i}.",
                                )
                            )

            else:
                value = config.get(name)
                if value is not None:
                    violations.extend(
                        element.validate_authorization(field_path, value, access_checker, accessible_tenant_ids, t)
                    )

        return violations
