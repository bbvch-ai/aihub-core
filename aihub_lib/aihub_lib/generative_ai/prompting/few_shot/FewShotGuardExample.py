from pydantic import BaseModel

from aihub_lib.i18n.LocaleString import LocaleString


class FewShotGuardExample(BaseModel):
    user: LocaleString
    success: bool
    reason: LocaleString
