import re
from typing import Any, Dict, List, Union

from llama_index.core.workflow import Event
from mongoengine import EmbeddedDocument

# TODO: create constant datafields
from aihub.app.agents.customer.fmh.constants.data_fields import (
    CHAPTER_ID,
    GROUP_ID,
    KEY,
    NAME,
    PART_OF_GROUPS,
    RULES,
    TARGET_POSITION_ID,
)


class GetPositionDetailsStepConfig(EmbeddedDocument):
    pass


def _create_lookup_dict(positions_list: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {position[KEY]: position for position in positions_list}


def _update_with_names(item: Dict[str, Any], lookup: Dict[str, Dict[str, Any]], id_fields: List[str]) -> None:
    for id_field in id_fields:
        key = item.get(id_field)
        if key and key in lookup:
            item[f"{id_field[:-3]}name"] = lookup[key][NAME]


def _update_rules_and_groups(data: Dict[str, Any], lookup: Dict[str, Dict[str, Any]]) -> None:
    if RULES in data:
        _update_rules(data[RULES], lookup)

    if PART_OF_GROUPS in data:
        data[PART_OF_GROUPS] = _update_groups(data[PART_OF_GROUPS], lookup)


def _update_rules(rules_data: Dict[str, List[Dict[str, Any]]], lookup: Dict[str, Dict[str, Any]]) -> None:
    for rule_set in rules_data.values():
        for rule in rule_set:
            if isinstance(rule, dict):
                _update_with_names(rule, lookup, [TARGET_POSITION_ID, CHAPTER_ID, GROUP_ID])


def _update_groups(
    groups_data: List[Union[str, Dict[str, Any]]], lookup: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    return [_process_group(group, lookup) for group in groups_data]


def _process_group(group: Union[str, Dict[str, Any]], lookup: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    if isinstance(group, dict) and GROUP_ID in group:
        group_id = group[GROUP_ID]
        return _create_group_dict(group_id, lookup)
    elif isinstance(group, str) and group in lookup:
        return _create_group_dict(group, lookup)
    return {KEY: group, NAME: "", RULES: []}


def _create_group_dict(group_id: str, lookup: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    if group_id in lookup:
        return {KEY: group_id, NAME: lookup[group_id][NAME], RULES: lookup[group_id].get(RULES, [])}
    return {KEY: group_id, NAME: "", RULES: []}


def _split_id(id_str):
    parts = id_str.split(".")

    results = []

    # Case 1: If the input is just a single letter, return nothing.
    if len(parts[0]) == 1 or parts[0].startswith("LG-"):
        return results

    # Case 2: Generate sub-IDs for parts of the first segment (e.g. XY becomes X and XY)
    if len(parts[0]) > 1:
        for i in range(1, len(parts[0])):
            results.append(parts[0][:i])
        results.append(parts[0])

    # Case 3: Generate sub-IDs by combining parts with dots (e.g. XY.11 becomes XY and XY.11)
    for i in range(1, len(parts)):
        sub_id = ".".join(parts[: i + 1])
        results.append(sub_id)

    return results


def _generate_link(key: str) -> str:
    """
    Generate a link based on the format of the key.

    - For keys in format 'XX.11.1111', it's a leistungsposition ('L').
    - For single-character keys (like 'A'), two-character keys, or keys in format 'XX.11', it's a chapter ('K').
    - For keys starting with 'LG-', it's a group ('G').

    Returns the formatted link string.
    """
    # Check for keys in the 'XX.11.1111' format (Leistungsposition)
    if re.match(r"^[A-Z]{2}\.\d{2}\.\d{4}$", key):
        return f"https://browser.tartools.ch/de/tardoc/data/L/{key}"

    # Check for chapter keys: single-character, two-character, or 'XX.11' format
    elif len(key) == 1 or re.match(r"^[A-Z]{2}$", key) or re.match(r"^[A-Z]{2}\.\d{2}$", key):
        return f"https://browser.tartools.ch/de/tardoc/data/K/{key}"

    # Check for group keys starting with 'LG-'
    elif key.startswith("LG-"):
        group_number = key.split("-")[1]  # Extract the part after 'LG-'
        return f"https://browser.tartools.ch/de/tardoc/data/G/{group_number}"

    return ""  # Default case if no pattern is matched


def get_position_details(
    positions: List[Dict[str, str]],
    json_data: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    lookup = _create_lookup_dict(json_data)
    detailed_positions = []

    keys = []
    chapter_keys_per_position = {}

    for position in positions:
        key = position[KEY]
        keys.append(key)
        chapter_keys = _split_id(key)
        chapter_keys_per_position[key] = chapter_keys

    for position in positions:
        key = position[KEY]
        if key in lookup:
            detailed_position = lookup[key].copy()
            _update_rules_and_groups(detailed_position, lookup)
            # Add the link based on the key
            detailed_position["link"] = _generate_link(key)
            detailed_position["part_of_chapters"] = []
            for chapter_key in chapter_keys_per_position[key]:
                if chapter_key not in lookup:
                    continue
                chapter_position = lookup[chapter_key].copy()
                _update_rules_and_groups(chapter_position, lookup)
                detailed_position["part_of_chapters"].append(chapter_position)
            detailed_positions.append(detailed_position)
        else:
            # Include non-existent positions with just the key and an empty link
            detailed_positions.append({KEY: key, "link": _generate_link(key)})

    return detailed_positions
