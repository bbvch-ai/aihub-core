from dagster import AssetKey


def group_name_from_asset_key(key: AssetKey, subgroup: str = "") -> str:
    group_name = "_".join(key.path[:-1])
    if subgroup:
        group_name = f"{group_name}_{subgroup}"
    return group_name


def asset_key_from_customer_and_namespace(customer_name: str, namespace_name: str, key: str) -> AssetKey:
    return AssetKey([customer_name, namespace_name, key])
