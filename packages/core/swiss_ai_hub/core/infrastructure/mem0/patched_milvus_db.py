import logging
from typing import Self, override

from mem0.vector_stores.milvus import MilvusDB

logger = logging.getLogger(__name__)


class PatchedMilvusDB(MilvusDB):
    """
    Patches mem0's MilvusDB to support advanced operator filters.

    mem0's _create_filter only renders scalar equality. Any non-string value
    (e.g. the `{"in": [...]}` shape used for namespace allow-lists) is dumped
    literally into the expression as `metadata["k"] == {'in': [...]}`, which
    Milvus rejects with a query-plan parse error. This patch translates the
    `in` operator into a valid Milvus `in [...]` expression.
    """

    @classmethod
    def from_milvus(cls, milvus: MilvusDB) -> Self:
        """Wrap an existing MilvusDB instance, preserving its client and config."""
        instance = cls.__new__(cls)
        instance.__dict__.update(milvus.__dict__)
        return instance

    @override
    def _create_filter(self, filters: dict) -> str:
        operands = []
        for key, value in filters.items():
            if isinstance(value, dict) and "in" in value:
                rendered = ", ".join(self._render_scalar(item) for item in value["in"])
                operands.append(f'(metadata["{key}"] in [{rendered}])')
            else:
                operands.append(f'(metadata["{key}"] == {self._render_scalar(value)})')
        return " and ".join(operands)

    @staticmethod
    def _render_scalar(value: object) -> str:
        return f'"{value}"' if isinstance(value, str) else f"{value}"
