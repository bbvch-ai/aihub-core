from dagster import AssetKey


def group_name_from_asset_key(key: AssetKey, subgroup: str = "") -> str:
    group_name = "_".join(key.path[:-1])
    if subgroup:
        group_name = f"{group_name}_{subgroup}"
    return group_name
