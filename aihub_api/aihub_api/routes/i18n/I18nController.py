
from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.routes.Controller import Controller
from fastapi import Depends, Security

from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.routes.i18n.dto.LocaleResponse import LocaleResponse
from aihub_api.routes.i18n.I18nService import I18nService


class I18nController(Controller):
    """
    A controller for handling internationalization (i18n) operations, such as retrieving the user's current locale.

    ### Why I18nController?
    In a multi-language environment, it's often useful to provide endpoints that reflect the user’s language
    preferences. The `I18nController` exposes endpoints that:
    - Detect the user’s current locale (e.g., from headers, user profile, or query parameters).
    - Return test strings in the detected language, verifying that translations and locale handling are working properly.

    ### Endpoint
    - `GET /i18n/my-locale`: Returns a `LocaleResponse` object containing the user's detected language and
      a test string localized in that language.

    ### Dependencies
    - `use_locale`: A dependency that sets up and returns a `LocaleHandler` based on the request.
    - `auth`: An authentication dependency determining the user. If none is provided, no authentication applies.

    ### Example
    ```python
    app = FastAPI()
    I18nController()
        .get_my_locale()
        .mount(app)
    ```

    When called, `GET /i18n/my-locale` returns something like `{"lang": "en", "test": "This is a test."}`
    depending on the user’s locale.
    """

    def __init__(self, route: str = "/i18n", auth: AuthHandler | None = None):
        super().__init__(route, auth)

    def get_my_locale(self, route: str = "/my-locale") -> "I18nController":
        @self.router.get(
            route,
            summary="Get User Locale",
            description=(
                "Retrieves the current locale setting for the user's session and returns a test string "
                "in the detected language."
            ),
            tags=["Utility"],
            responses={
                200: {"description": "Successful response with user locale information"},
            },
        )
        async def get_locale(
            user: AuthenticatedUser = Security(self.auth),
            t: LocaleHandler = Depends(use_locale),
        ) -> LocaleResponse:
            """
            Return the user's current locale and a localized test string.
            """
            return I18nService.get_user_locale(t)

        return self
