from pathlib import Path
from typing import Sequence

from dagster import (
    AnchorBasedFilePathMapping,
    AssetsDefinition,
    link_code_references_to_git,
    with_source_code_references,
)


def asset_definition_with_code_link(
    assets: Sequence[AssetsDefinition], customer_name: str, namespace_name: str
) -> Sequence[AssetsDefinition]:
    return link_code_references_to_git(
        assets_defs=with_source_code_references(assets),
        git_url=f"https://github.com/bbvch-ai/aihub-{customer_name}",
        git_branch="main",
        file_path_mapping=AnchorBasedFilePathMapping(
            local_file_anchor=Path(__file__),
            file_anchor_path_in_repository=f"pipelines/{namespace_name}/__init__.py",
        ),
    )
