import logging
from typing import Self

from mem0.configs.base import MemoryConfig
from mem0.graphs.tools import (
    DELETE_MEMORY_STRUCT_TOOL_GRAPH,
    EXTRACT_ENTITIES_STRUCT_TOOL,
    RELATIONS_STRUCT_TOOL,
)
from mem0.memory.graph_memory import MemoryGraph
from mem0.memory.utils import format_entities

from aihub_lib.i18n.LocaleHandler import LocaleHandler

logger = logging.getLogger(__name__)


class PatchedMemoryGraph(MemoryGraph):
    def __init__(
        self,
        config: MemoryConfig,
        t: LocaleHandler,
    ):
        super().__init__(config)
        if self.config.graph_store.custom_prompt:
            logger.warning("Custom prompt provided in graph store config is ignored.")
        self._t = t

    @classmethod
    def from_graph(
        cls,
        graph: MemoryGraph,
        t: LocaleHandler,
    ) -> Self:
        return cls(graph.config, t=t)

    def _retrieve_nodes_from_data(self, data, filters):
        """Extracts all the entities mentioned in the query."""
        search_results = self.llm.generate_response(
            messages=[
                {
                    "role": "system",
                    "content": self._t("lib.prompt.memory.entity_extraction", user_id=filters["user_id"]),
                },
                {"role": "user", "content": data},
            ],
            tools=[EXTRACT_ENTITIES_STRUCT_TOOL],
        )

        entity_type_map = {}

        try:
            for tool_call in search_results["tool_calls"]:
                if tool_call["name"] != "extract_entities":
                    continue
                for item in tool_call["arguments"]["entities"]:
                    entity_type_map[item["entity"]] = item["entity_type"]
        except Exception as e:
            logger.exception(
                f"Error in search tool: {e}, llm_provider={self.llm_provider}, search_results={search_results}"
            )

        entity_type_map = {k.lower().replace(" ", "_"): v.lower().replace(" ", "_") for k, v in entity_type_map.items()}
        logger.debug(f"Entity type map: {entity_type_map}\n search_results={search_results}")
        return entity_type_map

    def _establish_nodes_relations_from_data(self, data, filters, entity_type_map):
        """Establish relations among the extracted nodes."""
        messages = [
            {
                "role": "system",
                "content": self._t("lib.prompt.memory.relationship_extraction", user_id=filters["user_id"]),
            },
            {
                "role": "user",
                "content": f"<entities>\n{list(entity_type_map.keys())}\n</entities>\n<text>\n{data}\n</text>",
            },
        ]

        extracted_entities = self.llm.generate_response(
            messages=messages,
            tools=[RELATIONS_STRUCT_TOOL],
        )

        entities = []
        if extracted_entities.get("tool_calls"):
            entities = extracted_entities["tool_calls"][0].get("arguments", {}).get("entities", [])

        entities = self._remove_spaces_from_entities(entities)

        # NEW: Validate that source/destination are in the entity list
        valid_entities = set(entity_type_map.keys())
        validated = []
        for rel in entities:
            if rel["source"] in valid_entities and rel["destination"] in valid_entities:
                validated.append(rel)
            else:
                logger.warning(f"Dropped relationship with unknown entity: {rel}. " f"Known entities: {valid_entities}")

        logger.debug(f"Extracted entities: {validated}")
        return validated

    def _get_delete_entities_from_search_output(self, search_output, data, filters):
        """Get the entities to be deleted from the search output."""
        search_output_string = format_entities(search_output)

        memory_updates = self.llm.generate_response(
            messages=[
                {
                    "role": "system",
                    "content": self._t("lib.prompt.memory.relationship_deletion", user_id=filters["user_id"]),
                },
                {
                    "role": "user",
                    "content": f"<existing_memories>\n{search_output_string}\n"
                    f"</existing_memories>\n"
                    f"<new_information>\n"
                    f"{data}\n"
                    f"</new_information>",
                },
            ],
            tools=[DELETE_MEMORY_STRUCT_TOOL_GRAPH],
        )

        to_be_deleted = []
        for item in memory_updates.get("tool_calls", []):
            if item.get("name") == "delete_graph_memory":
                to_be_deleted.append(item.get("arguments"))

        to_be_deleted = self._remove_spaces_from_entities(to_be_deleted)
        logger.debug(f"Deleted relationships: {to_be_deleted}")
        return to_be_deleted
