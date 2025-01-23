import os
from typing import Tuple


def get_customer_and_namespace(file_path: str) -> Tuple[str, str]:
    path_parts = os.path.normpath(file_path).split(os.sep)

    if "customer" not in path_parts:
        raise ValueError("The file path does not contain the 'customer' and 'namespace' components")

    customer_index = path_parts.index("customer") + 1
    namespace_index = path_parts.index("customer") + 2

    customer = path_parts[customer_index]
    namespace = path_parts[namespace_index]
    return customer, namespace


def get_group_name(customer_name: str, namespace_name: str) -> str:
    return f"{customer_name}_{namespace_name}"
