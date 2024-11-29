from typing import Dict, List, Optional

from fsspec import AbstractFileSystem
from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document

from aihub.app.handlers.TracingHandler import trace_fn


class RawLoader(BaseReader):
    @trace_fn()
    def load_data(
        self,
        file: str,
        extra_info: Optional[Dict] = None,
        fs: Optional[AbstractFileSystem] = None,
    ) -> List[Document]:
        """Parse file into string."""
        with fs.open(str(file), "r", encoding="utf-8") as f:
            content = f.read()
        metadata = extra_info or {}
        return [Document(text=content, metadata=metadata)]
