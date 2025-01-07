from pydantic import BaseModel
from aihub_lib.i18n.LocaleString import LocaleString


class FewShotExample(BaseModel):
    user: LocaleString
    agent: LocaleString
