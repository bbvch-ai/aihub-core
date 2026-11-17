import sys
from pathlib import Path


class StartupAdapter:
    @staticmethod
    def patch(path: Path) -> None:
        source = path.read_text()
        if source.count("open_webui.main:app") != 2 or 'ARGS=(--workers "$UVICORN_WORKERS"' not in source:
            raise RuntimeError("Open WebUI startup changed. Review the mod entrypoint adapter before upgrading.")
        path.write_text(source.replace("open_webui.main:app", "aihub_mods.main:app"))


if __name__ == "__main__":
    StartupAdapter.patch(Path(sys.argv[1]))
