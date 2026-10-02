from pathlib import Path
from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.form import Form, InputText

_DEMO_FOLDER = Path(__file__).parent


class DemoRecordsOptions(Form):
    """Where the demo source reads its records: a JSON file inside this folder, never anywhere else."""

    file_path: Annotated[str | InputText, Field(description="JSON file of records, relative to the demo folder.")] = (
        "demo_records.json"
    )

    def records_file(self) -> Path:
        """Whoever creates a database picks this path, so it must not reach files outside the demo folder."""
        requested = (_DEMO_FOLDER / self.file_path).resolve()
        if _DEMO_FOLDER.resolve() not in requested.parents:
            raise ValueError(f"The demo source only reads files inside {_DEMO_FOLDER}, not '{self.file_path}'.")
        return requested
