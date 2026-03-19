from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.infrastructure import trace_fn

from swiss_ai_hub.api.routes.i18n.dto.locale_response import LocaleResponse


class I18nService:
    """
    A service layer class providing business logic for internationalization endpoints.

    ### Why I18nService?
    Separating the logic from the controller allows for easier testing, maintenance, and reusability.
    The service handles:
    - Constructing a `LocaleResponse` object from the user and `LocaleHandler`.
    - Encapsulating how we choose test strings or handle locale logic, if it evolves in the future.

    Currently, it simply returns a `LocaleResponse` using the locale from `LocaleHandler` and a test string key.
    """

    @staticmethod
    @trace_fn
    def get_user_locale(locale_handler: LocaleHandler) -> LocaleResponse:
        """
        Returns a LocaleResponse for the given user and locale_handler.

        The `locale_handler("token.common.test")` call retrieves a localized string for a test message,
        validating that the i18n mechanism is working as expected.
        """
        return LocaleResponse(lang=locale_handler.locale, test=locale_handler("token.common.test"))
