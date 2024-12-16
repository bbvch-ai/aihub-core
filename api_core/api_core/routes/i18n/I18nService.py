from api_core.routes.i18n.dto.LocaleResponse import LocaleResponse
from lib_core.i18n.LocaleHandler import LocaleHandler
from lib_core.records.User import User

class I18nService:

    @staticmethod
    def get_user_locale(user: User, locale_handler: LocaleHandler) -> LocaleResponse:
        return LocaleResponse(lang=locale_handler.locale, test=locale_handler("api.common.test"))
