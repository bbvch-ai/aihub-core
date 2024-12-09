from typing import Optional

from pydantic import BaseModel


class PartialAgentTopic(BaseModel):
    agent_class: Optional[str] = None
    agent_id: Optional[str] = None
    run_id: Optional[str] = None
    thread_id: Optional[str] = None
    display_id: Optional[str] = None
    event_type: Optional[str] = None
    event_name: Optional[str] = None
    event_id: Optional[str] = None