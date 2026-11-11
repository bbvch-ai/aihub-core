"""Select which backend modules to test and which images to build for one CI run.

A pull request only pays for the modules and images its diff can affect; shared inputs (core, the lockfile,
compose and CI definitions) still select everything, so a cross-package break cannot slip through unnoticed.
Run with `uv run --no-project --with pyyaml --with pydantic python .github/scripts/ci_targets.py`; results go to $GITHUB_OUTPUT.
"""

import argparse
import json
import os
import subprocess
from pathlib import Path

import yaml
from pydantic import BaseModel

COMPOSE_CONFIG = Path("infra/deployment/compose-config.yml")

PYTHON_SHARED_PATHS = ("packages/core/", "uv.lock", "pyproject.toml")
FRONTEND_SHARED_PATHS = ("package.json", "pnpm-lock.yaml", "pnpm-workspace.yaml")
TEST_SHARED_PATHS = (
    *PYTHON_SHARED_PATHS,
    "Makefile",
    ".env.dev",
    "infra/",
    ".github/actions/test_backend/",
    ".github/scripts/",
    ".github/workflows/analyze-test-pr.yml",
)
IMAGE_SHARED_PATHS = (".github/scripts/", ".github/workflows/analyze-test-pr.yml")

STACK_DATA = "postgres nats valkey postgres-ferretdb ferretdb"
STACK_STORAGE = "litellm seaweedfs-master seaweedfs-volume seaweedfs-filer seaweedfs-s3 etcd milvus-standalone"


class TestModule(BaseModel):
    path: str
    services: str = ""
    shard_count: int = 1
    install_ffmpeg: bool = False
    triggered_by: tuple[str, ...] = ()


class ImageTarget(BaseModel):
    name: str
    file: str
    cache_scope: str
    triggered_by: tuple[str, ...]


TEST_MODULES = (
    TestModule(
        path="packages/core",
        services=f"{STACK_DATA} {STACK_STORAGE} neo4j keycloak",
        shard_count=2,
    ),
    TestModule(
        path="packages/api",
        services=f"{STACK_DATA} {STACK_STORAGE} neo4j",
        install_ffmpeg=True,
    ),
    TestModule(path="packages/pipeline"),
    TestModule(
        path="packages/agent",
        services=f"postgres clickhouse langfuse-worker langfuse-web otel-collector {STACK_DATA} {STACK_STORAGE} neo4j",
        shard_count=3,
    ),
    TestModule(path="packages/bot", services="nats valkey postgres-ferretdb ferretdb"),
    TestModule(
        path="packages/process",
        services=f"{STACK_DATA} {STACK_STORAGE}",
        triggered_by=("packages/agent/",),
    ),
    TestModule(
        path="packages/sysadmin-api",
        services="postgres-ferretdb ferretdb",
        triggered_by=("packages/api/",),
    ),
)


class CiTargets:
    @staticmethod
    def changed_files(base: str, head: str) -> list[str]:
        diff = subprocess.run(
            ["git", "diff", "--name-only", f"{base}...{head}"], check=True, capture_output=True, text=True
        )
        return diff.stdout.split()

    @staticmethod
    def touches(changed: list[str] | None, prefixes: tuple[str, ...]) -> bool:
        if changed is None:
            return True
        return any(file == prefix or file.startswith(prefix) for file in changed for prefix in prefixes)

    @classmethod
    def modules(cls, changed: list[str] | None) -> list[TestModule]:
        return [
            module
            for module in TEST_MODULES
            if cls.touches(changed, (*TEST_SHARED_PATHS, f"{module.path}/", *module.triggered_by))
        ]

    @staticmethod
    def localbuild_images(suffix: str) -> list[str]:
        image_tags = yaml.safe_load(COMPOSE_CONFIG.read_text())["image_tags"]
        return sorted(
            name
            for name, tag in image_tags.items()
            if isinstance(tag, dict) and tag.get("build") == "localbuild" and name.endswith(suffix)
        )

    @classmethod
    def all_images(cls) -> list[ImageTarget]:
        agent_paths = (*PYTHON_SHARED_PATHS, "packages/agent/")
        pipeline_paths = (*PYTHON_SHARED_PATHS, "packages/pipeline/")
        web_paths = (*FRONTEND_SHARED_PATHS, "packages/web/")
        return [
            ImageTarget(
                name="api",
                file="packages/api/Dockerfile",
                cache_scope="api",
                triggered_by=(*PYTHON_SHARED_PATHS, "packages/api/"),
            ),
            ImageTarget(
                name="bot",
                file="packages/bot/Dockerfile",
                cache_scope="bot",
                triggered_by=(*PYTHON_SHARED_PATHS, "packages/bot/"),
            ),
            ImageTarget(
                name="sysadmin-api",
                file="packages/sysadmin-api/Dockerfile",
                cache_scope="sysadmin-api",
                triggered_by=(*PYTHON_SHARED_PATHS, "packages/api/", "packages/sysadmin-api/"),
            ),
            ImageTarget(
                name="backup",
                file="packages/backup/Dockerfile",
                cache_scope="backup",
                triggered_by=("uv.lock", "pyproject.toml", "packages/backup/"),
            ),
            ImageTarget(name="web", file="packages/web/Dockerfile", cache_scope="web", triggered_by=web_paths),
            ImageTarget(
                name="sysadmin-web",
                file="packages/sysadmin-web/Dockerfile",
                cache_scope="sysadmin-web",
                triggered_by=(*web_paths, "packages/sysadmin-web/"),
            ),
            ImageTarget(
                name="dagster", file="packages/pipeline/Dockerfile", cache_scope="dagster", triggered_by=pipeline_paths
            ),
            *(
                ImageTarget(
                    name=name,
                    file=f"packages/pipeline/app/{name}/Dockerfile",
                    cache_scope="pipeline",
                    triggered_by=pipeline_paths,
                )
                for name in cls.localbuild_images("_pipeline")
            ),
            *(
                ImageTarget(
                    name=name,
                    file=f"packages/agent/app/{name}/Dockerfile",
                    cache_scope="agent",
                    triggered_by=agent_paths,
                )
                for name in cls.localbuild_images("_agent")
            ),
        ]

    @classmethod
    def images(cls, changed: list[str] | None) -> list[ImageTarget]:
        return [image for image in cls.all_images() if cls.touches(changed, (*IMAGE_SHARED_PATHS, *image.triggered_by))]

    @staticmethod
    def test_matrix(modules: list[TestModule], sharded: bool = True) -> list[dict[str, str | bool | int]]:
        return [
            {
                "module": module.path,
                "docker_compose_services": module.services,
                "install_ffmpeg": module.install_ffmpeg,
                "shard_index": shard_index,
                "shard_count": module.shard_count if sharded else 1,
            }
            for module in modules
            for shard_index in range(1, (module.shard_count if sharded else 1) + 1)
        ]

    @classmethod
    def outputs(cls, changed_for_tests: list[str] | None, changed_for_images: list[str] | None) -> dict[str, str]:
        modules = cls.modules(changed_for_tests)
        images = cls.images(changed_for_images)
        return {
            "test_matrix": json.dumps(cls.test_matrix(modules)),
            "tested_modules": json.dumps([module.path for module in modules]),
            "sharded_modules": json.dumps([module.path for module in modules if module.shard_count > 1]),
            "images": json.dumps([image.model_dump(exclude={"triggered_by"}) for image in images]),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="Commit to diff against; omit to select everything")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--all-tests", action="store_true", help="Test every module regardless of the diff")
    parser.add_argument("--only", nargs="*", help="Restrict testing to these module paths")
    args = parser.parse_args()

    changed = CiTargets.changed_files(args.base, args.head) if args.base else None
    outputs = CiTargets.outputs(None if args.all_tests else changed, changed)
    if args.only is not None:
        selected = [module for module in TEST_MODULES if module.path in args.only]
        outputs["test_matrix"] = json.dumps(CiTargets.test_matrix(selected, sharded=False))
        outputs["tested_modules"] = json.dumps([module.path for module in selected])

    for name, value in outputs.items():
        print(f"{name}={value}")
    if github_output := os.environ.get("GITHUB_OUTPUT"):
        with open(github_output, "a", encoding="utf-8") as output_file:
            output_file.writelines(f"{name}={value}\n" for name, value in outputs.items())


if __name__ == "__main__":
    main()
