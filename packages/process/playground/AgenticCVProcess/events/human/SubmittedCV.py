from datetime import datetime
from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.nats.events import HumanWorkEvent, ProcessStartEvent
from swiss_ai_hub.core.nats.events.form import (
    CascadeSelect,
    Checkbox,
    DatePicker,
    InputNumber,
    InputText,
    Select,
    SelectButton,
    Slider,
    Textarea,
)


class SubmittedCV(HumanWorkEvent, ProcessStartEvent):
    name: Annotated[InputText | str, Field(description="Name of the applicant")]
    application_date: Annotated[DatePicker | datetime, Field(description="Date of the application")]
    profession: Annotated[Select | str, Field(description="Profession of the applicant")]
    level: Annotated[SelectButton | str | None, Field(description="Level of the applicant")] = None
    match: Annotated[Slider | float | None, Field(description="Match score")] = None
    salary: Annotated[InputNumber | float | None, Field(description="Match score")] = None
    business_area: Annotated[CascadeSelect | str | None, Field(description="Business area")] = None
    hire: Annotated[Checkbox | bool, Field(description="Hire or not")]
    reasoning: Annotated[Textarea | str, Field(description="Reasoning")]
