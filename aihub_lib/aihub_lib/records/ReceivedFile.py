from pydantic import BaseModel


class ReceivedFile(BaseModel):
    filename: str
    file_data: str
    file_type: str
